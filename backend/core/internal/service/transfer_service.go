package service

import (
	"context"
	"errors"
	"fmt"
	"time"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
)


type TransferService struct {
	txRepo      domain.TransactionRepository
	accountRepo domain.AccountRepository
}

func NewTransferService(txRepo domain.TransactionRepository, accountRepo domain.AccountRepository) domain.TransferService {
	return &TransferService{
		txRepo:      txRepo,
		accountRepo: accountRepo,
	}
}

func (s *TransferService) Transfer(ctx context.Context, userID uint64, req *domain.TransferRequest) (*domain.Transaction, error) {
	fromAcc, err := s.accountRepo.FindByUserID(ctx, userID)
	if err != nil {
		logger.Error(ctx, "Failed to resolve sender account", err, map[string]interface{}{"user_id": userID})
		return nil, err
	}
	if fromAcc == nil {
		return nil, errors.New("sender account not found")
	}

	if req.AmountCents <= 0 {
		return nil, errors.New("amount must be greater than zero")
	}

	if req.ToAccountNumber == fromAcc.AccountNumber {
		return nil, errors.New("cannot transfer funds to your own account")
	}

	return s.txRepo.ExecuteTransfer(ctx, fromAcc.ID, req.ToAccountNumber, req.AmountCents, req.Description, req.Category)
}

func (s *TransferService) Deposit(ctx context.Context, userID uint64, req *domain.DepositWithdrawRequest) (*domain.Transaction, error) {
	acc, err := s.accountRepo.FindByUserID(ctx, userID)
	if err != nil {
		logger.Error(ctx, "Failed to resolve deposit account", err, map[string]interface{}{"user_id": userID})
		return nil, err
	}
	if acc == nil {
		return nil, errors.New("account not found")
	}

	return s.txRepo.ExecuteDeposit(ctx, acc.ID, req.AmountCents, req.Description, req.Category)
}

func (s *TransferService) GetTransactions(ctx context.Context, userID uint64, limit int, offset int, category string) ([]domain.Transaction, error) {
	acc, err := s.accountRepo.FindByUserID(ctx, userID)
	if err != nil {
		return nil, err
	}
	if acc == nil {
		return nil, errors.New("account not found")
	}

	return s.txRepo.ListByAccountID(ctx, acc.ID, limit, offset, category)
}

func (s *TransferService) GetSpendingSummary(ctx context.Context, userID uint64) (*domain.SpendingSummary, error) {
	acc, err := s.accountRepo.FindByUserID(ctx, userID)
	if err != nil {
		return nil, err
	}
	if acc == nil {
		return nil, errors.New("account not found")
	}

	return s.txRepo.GetSpendingSummary(ctx, acc.ID)
}

func (s *TransferService) GetTransactionDetail(ctx context.Context, userID uint64, identifier string) (*domain.Transaction, error) {
	acc, err := s.accountRepo.FindByUserID(ctx, userID)
	if err != nil {
		return nil, err
	}
	if acc == nil {
		return nil, errors.New("account not found")
	}

	// Try finding by integer ID
	var parsedID uint64
	if _, err := fmt.Sscanf(identifier, "%d", &parsedID); err == nil && parsedID > 0 {
		tx, err := s.txRepo.FindByID(ctx, parsedID)
		if err == nil && tx != nil && tx.AccountID == acc.ID {
			return tx, nil
		}
	}

	// Try finding by Reference Number
	tx, err := s.txRepo.FindByReference(ctx, identifier)
	if err != nil {
		return nil, err
	}
	if tx == nil || tx.AccountID != acc.ID {
		return nil, errors.New("transaction not found or access denied")
	}

	return tx, nil
}

func (s *TransferService) GenerateStatement(ctx context.Context, userID uint64, req *domain.StatementRequest) (*domain.StatementResponse, error) {
	acc, err := s.accountRepo.FindByUserID(ctx, userID)
	if err != nil {
		return nil, err
	}
	if acc == nil {
		return nil, errors.New("account not found")
	}

	now := time.Now()
	startDate := now.AddDate(0, -1, 0)
	endDate := now

	if req.StartDate != nil {
		startDate = *req.StartDate
	}
	if req.EndDate != nil {
		endDate = *req.EndDate
	}

	txs, err := s.txRepo.ListByDateRange(ctx, acc.ID, startDate.Format(time.RFC3339), endDate.Format(time.RFC3339))
	if err != nil {
		return nil, err
	}

	var totalDeposits int64
	var totalWithdrawals int64
	for _, t := range txs {
		if t.Type == domain.TransactionDeposit || t.Type == domain.TransactionTransferIn {
			totalDeposits += t.AmountCents
		} else {
			totalWithdrawals += t.AmountCents
		}
	}

	statementID := fmt.Sprintf("STM-%d-%04d", now.Unix(), now.Nanosecond()%10000)

	return &domain.StatementResponse{
		StatementID:          statementID,
		AccountNumber:        acc.AccountNumber,
		AccountHolder:        "AURA Client",
		PeriodStart:          startDate,
		PeriodEnd:            endDate,
		StartingBalanceCents: acc.BalanceCents - (totalDeposits - totalWithdrawals),
		EndingBalanceCents:   acc.BalanceCents,
		TotalDepositsCents:   totalDeposits,
		TotalWithdrawalsCents: totalWithdrawals,
		TransactionCount:     len(txs),
		Transactions:         txs,
		GeneratedAt:          now,
	}, nil
}


