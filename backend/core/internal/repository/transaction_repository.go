package repository

import (
	"context"
	"errors"
	"fmt"
	"time"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)


type GormTransactionRepository struct {
	db *gorm.DB
}

func NewTransactionRepository(db *gorm.DB) domain.TransactionRepository {
	return &GormTransactionRepository{db: db}
}

func (r *GormTransactionRepository) Create(ctx context.Context, tx *domain.Transaction) error {
	if err := r.db.WithContext(ctx).Create(tx).Error; err != nil {
		logger.Error(ctx, "Failed to insert transaction record", err, map[string]interface{}{
			"account_id": tx.AccountID,
			"ref":        tx.ReferenceNumber,
		})
		return err
	}
	return nil
}

func (r *GormTransactionRepository) ListByAccountID(ctx context.Context, accountID uint64, limit int, offset int, category string) ([]domain.Transaction, error) {
	if limit <= 0 || limit > 100 {
		limit = 50
	}
	if offset < 0 {
		offset = 0
	}

	query := r.db.WithContext(ctx).Where("account_id = ?", accountID)
	if category != "" {
		query = query.Where("LOWER(category) = LOWER(?)", category)
	}

	var txs []domain.Transaction
	if err := query.Order("created_at DESC").Limit(limit).Offset(offset).Find(&txs).Error; err != nil {
		logger.Error(ctx, "Failed to query transaction list", err, map[string]interface{}{
			"account_id": accountID,
		})
		return nil, err
	}
	return txs, nil
}

func (r *GormTransactionRepository) FindByID(ctx context.Context, id uint64) (*domain.Transaction, error) {
	var tx domain.Transaction
	err := r.db.WithContext(ctx).Where("id = ?", id).First(&tx).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		logger.Error(ctx, "Error finding transaction by ID", err, map[string]interface{}{"id": id})
		return nil, err
	}
	return &tx, nil
}

func (r *GormTransactionRepository) FindByReference(ctx context.Context, ref string) (*domain.Transaction, error) {
	var tx domain.Transaction
	err := r.db.WithContext(ctx).Where("reference_number = ?", ref).First(&tx).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		logger.Error(ctx, "Error finding transaction by reference", err, map[string]interface{}{"ref": ref})
		return nil, err
	}
	return &tx, nil
}

func (r *GormTransactionRepository) ListByDateRange(ctx context.Context, accountID uint64, start, end string) ([]domain.Transaction, error) {
	query := r.db.WithContext(ctx).Where("account_id = ?", accountID)
	if start != "" {
		query = query.Where("created_at >= ?", start)
	}
	if end != "" {
		query = query.Where("created_at <= ?", end)
	}

	var txs []domain.Transaction
	if err := query.Order("created_at ASC").Find(&txs).Error; err != nil {
		logger.Error(ctx, "Failed to query date range transactions", err, map[string]interface{}{
			"account_id": accountID,
			"start":      start,
			"end":        end,
		})
		return nil, err
	}
	return txs, nil
}

func (r *GormTransactionRepository) GetSpendingSummary(ctx context.Context, accountID uint64) (*domain.SpendingSummary, error) {

	type summaryRow struct {
		Type      string
		Category  string
		TotalSum  int64
		ItemCount int
	}

	var rows []summaryRow
	err := r.db.WithContext(ctx).
		Model(&domain.Transaction{}).
		Select("type, category, SUM(amount_cents) as total_sum, COUNT(*) as item_count").
		Where("account_id = ?", accountID).
		Group("type, category").
		Scan(&rows).Error

	if err != nil {
		logger.Error(ctx, "Failed to compute spending summary", err, map[string]interface{}{
			"account_id": accountID,
		})
		return nil, err
	}

	summary := &domain.SpendingSummary{
		CategoryBreakdown: make(map[string]int64),
	}

	for _, r := range rows {
		summary.TransactionCount += r.ItemCount
		if r.Type == string(domain.TransactionDeposit) || r.Type == string(domain.TransactionTransferIn) {
			summary.TotalIncomeCents += r.TotalSum
		} else {
			summary.TotalSpendingCents += r.TotalSum
			summary.CategoryBreakdown[r.Category] += r.TotalSum
		}
	}

	return summary, nil
}

// ExecuteTransfer performs atomic money transfer with row-level locks (FOR UPDATE) in a GORM transaction.
func (r *GormTransactionRepository) ExecuteTransfer(ctx context.Context, fromAccID uint64, toAccNum string, amountCents int64, description string, category string) (*domain.Transaction, error) {
	if amountCents <= 0 {
		return nil, errors.New("transfer amount must be strictly greater than zero")
	}

	var senderTxRecord domain.Transaction

	err := r.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		// 1. Lock sender account row using SELECT ... FOR UPDATE to avoid race conditions
		var sender domain.Account
		if err := tx.Clauses(clause.Locking{Strength: "UPDATE"}).Where("id = ?", fromAccID).First(&sender).Error; err != nil {
			if errors.Is(err, gorm.ErrRecordNotFound) {
				return errors.New("source account not found")
			}
			return fmt.Errorf("failed to lock source account: %w", err)
		}

		if sender.Status != "ACTIVE" {
			return errors.New("source account is not active")
		}

		if sender.BalanceCents < amountCents {
			return errors.New("insufficient account balance for transfer")
		}

		// 2. Lock recipient account row
		var recipient domain.Account
		if err := tx.Clauses(clause.Locking{Strength: "UPDATE"}).Where("account_number = ?", toAccNum).First(&recipient).Error; err != nil {
			if errors.Is(err, gorm.ErrRecordNotFound) {
				return errors.New("destination account not found")
			}
			return fmt.Errorf("failed to lock destination account: %w", err)
		}

		if recipient.Status != "ACTIVE" {
			return errors.New("destination account is not active")
		}

		if sender.ID == recipient.ID {
			return errors.New("cannot transfer funds to the same account")
		}

		// 3. Fetch user details for both parties for audit logs
		var senderUser domain.User
		var recipientUser domain.User
		_ = tx.Where("id = ?", sender.UserID).First(&senderUser).Error
		_ = tx.Where("id = ?", recipient.UserID).First(&recipientUser).Error

		// 4. Update balances
		if err := tx.Model(&sender).Update("balance_cents", gorm.Expr("balance_cents - ?", amountCents)).Error; err != nil {
			return fmt.Errorf("failed to deduct sender balance: %w", err)
		}

		if err := tx.Model(&recipient).Update("balance_cents", gorm.Expr("balance_cents + ?", amountCents)).Error; err != nil {
			return fmt.Errorf("failed to credit recipient balance: %w", err)
		}

		now := time.Now()
		refNumber := fmt.Sprintf("TRF-%d-%04d", now.UnixNano(), now.Nanosecond()%10000)
		if category == "" {
			category = "Transfer"
		}

		// 5. Create sender transaction record (TRANSFER_OUT)
		senderTxRecord = domain.Transaction{
			AccountID:              sender.ID,
			Type:                   domain.TransactionTransferOut,
			AmountCents:            amountCents,
			Description:            description,
			Category:               category,
			CounterpartyAccountNum: recipient.AccountNumber,
			CounterpartyName:       recipientUser.FullName,
			ReferenceNumber:        refNumber,
			CreatedAt:              now,
		}
		if err := tx.Create(&senderTxRecord).Error; err != nil {
			return fmt.Errorf("failed to record sender transaction: %w", err)
		}

		// 6. Create recipient transaction record (TRANSFER_IN)
		recipientTxRecord := domain.Transaction{
			AccountID:              recipient.ID,
			Type:                   domain.TransactionTransferIn,
			AmountCents:            amountCents,
			Description:            description,
			Category:               category,
			CounterpartyAccountNum: sender.AccountNumber,
			CounterpartyName:       senderUser.FullName,
			ReferenceNumber:        refNumber,
			CreatedAt:              now,
		}
		if err := tx.Create(&recipientTxRecord).Error; err != nil {
			return fmt.Errorf("failed to record recipient transaction: %w", err)
		}

		return nil
	})

	if err != nil {
		logger.Error(ctx, "Fund transfer transaction failed", err, map[string]interface{}{
			"from_account_id":   fromAccID,
			"to_account_number": toAccNum,
			"amount_cents":      amountCents,
		})
		return nil, err
	}

	logger.Info(ctx, "Fund transfer executed successfully", map[string]interface{}{
		"ref":          senderTxRecord.ReferenceNumber,
		"amount_cents": amountCents,
	})

	return &senderTxRecord, nil
}

// ExecuteDeposit handles deposit into an account within a GORM transaction
func (r *GormTransactionRepository) ExecuteDeposit(ctx context.Context, accID uint64, amountCents int64, description string, category string) (*domain.Transaction, error) {
	if amountCents <= 0 {
		return nil, errors.New("deposit amount must be greater than zero")
	}

	var depositTx domain.Transaction

	err := r.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		if err := tx.Model(&domain.Account{}).Where("id = ?", accID).Update("balance_cents", gorm.Expr("balance_cents + ?", amountCents)).Error; err != nil {
			return fmt.Errorf("failed to credit balance: %w", err)
		}

		now := time.Now()
		refNumber := fmt.Sprintf("DEP-%d-%04d", now.UnixNano(), now.Nanosecond()%10000)
		if category == "" {
			category = "Deposit"
		}

		depositTx = domain.Transaction{
			AccountID:       accID,
			Type:            domain.TransactionDeposit,
			AmountCents:     amountCents,
			Description:     description,
			Category:        category,
			ReferenceNumber: refNumber,
			CreatedAt:       now,
		}

		return tx.Create(&depositTx).Error
	})

	if err != nil {
		logger.Error(ctx, "Deposit transaction failed", err, map[string]interface{}{
			"account_id":   accID,
			"amount_cents": amountCents,
		})
		return nil, err
	}

	logger.Info(ctx, "Deposit transaction successful", map[string]interface{}{
		"ref":          depositTx.ReferenceNumber,
		"amount_cents": amountCents,
	})

	return &depositTx, nil
}

