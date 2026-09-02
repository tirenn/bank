package repository

import (
	"context"
	"errors"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
	"gorm.io/gorm"
)


type GormAccountRepository struct {
	db *gorm.DB
}

func NewAccountRepository(db *gorm.DB) domain.AccountRepository {
	return &GormAccountRepository{db: db}
}

func (r *GormAccountRepository) Create(ctx context.Context, acc *domain.Account) error {
	if err := r.db.WithContext(ctx).Create(acc).Error; err != nil {
		logger.Error(ctx, "Failed to create account in database", err, map[string]interface{}{"account_number": acc.AccountNumber})
		return err
	}
	return nil
}

func (r *GormAccountRepository) FindByUserID(ctx context.Context, userID uint64) (*domain.Account, error) {
	var acc domain.Account
	err := r.db.WithContext(ctx).Where("user_id = ?", userID).Order("id ASC").First(&acc).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		logger.Error(ctx, "Error finding account by user ID", err, map[string]interface{}{"user_id": userID})
		return nil, err
	}
	return &acc, nil
}

func (r *GormAccountRepository) ListByUserID(ctx context.Context, userID uint64) ([]domain.Account, error) {
	var accounts []domain.Account
	err := r.db.WithContext(ctx).Where("user_id = ?", userID).Order("id ASC").Find(&accounts).Error
	if err != nil {
		logger.Error(ctx, "Error listing accounts by user ID", err, map[string]interface{}{"user_id": userID})
		return nil, err
	}
	return accounts, nil
}


func (r *GormAccountRepository) FindByAccountNumber(ctx context.Context, accountNumber string) (*domain.Account, error) {
	var acc domain.Account
	err := r.db.WithContext(ctx).Where("account_number = ?", accountNumber).First(&acc).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		logger.Error(ctx, "Error finding account by account number", err, map[string]interface{}{"account_number": accountNumber})
		return nil, err
	}
	return &acc, nil
}

func (r *GormAccountRepository) FindByID(ctx context.Context, id uint64) (*domain.Account, error) {
	var acc domain.Account
	err := r.db.WithContext(ctx).Where("id = ?", id).First(&acc).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		logger.Error(ctx, "Error finding account by ID", err, map[string]interface{}{"account_id": id})
		return nil, err
	}
	return &acc, nil
}

func (r *GormAccountRepository) Update(ctx context.Context, acc *domain.Account) error {
	if err := r.db.WithContext(ctx).Save(acc).Error; err != nil {
		logger.Error(ctx, "Failed to update account in database", err, map[string]interface{}{"account_id": acc.ID})
		return err
	}
	return nil
}


