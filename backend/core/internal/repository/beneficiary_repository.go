package repository

import (
	"context"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
	"gorm.io/gorm"
)


type GormBeneficiaryRepository struct {
	db *gorm.DB
}

func NewBeneficiaryRepository(db *gorm.DB) domain.BeneficiaryRepository {
	return &GormBeneficiaryRepository{db: db}
}

func (r *GormBeneficiaryRepository) Create(ctx context.Context, b *domain.Beneficiary) error {
	if err := r.db.WithContext(ctx).Create(b).Error; err != nil {
		logger.Error(ctx, "Failed to create beneficiary", err, map[string]interface{}{"user_id": b.UserID})
		return err
	}
	return nil
}

func (r *GormBeneficiaryRepository) ListByUserID(ctx context.Context, userID uint64) ([]domain.Beneficiary, error) {
	var list []domain.Beneficiary
	if err := r.db.WithContext(ctx).Where("user_id = ?", userID).Order("created_at DESC").Find(&list).Error; err != nil {
		logger.Error(ctx, "Failed to list beneficiaries", err, map[string]interface{}{"user_id": userID})
		return nil, err
	}
	return list, nil
}

func (r *GormBeneficiaryRepository) Delete(ctx context.Context, userID, id uint64) error {
	if err := r.db.WithContext(ctx).Where("id = ? AND user_id = ?", id, userID).Delete(&domain.Beneficiary{}).Error; err != nil {
		logger.Error(ctx, "Failed to delete beneficiary", err, map[string]interface{}{"id": id})
		return err
	}
	return nil
}

