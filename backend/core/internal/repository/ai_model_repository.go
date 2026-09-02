package repository

import (
	"context"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
	"gorm.io/gorm"
)

type GormAIModelRepository struct {
	db *gorm.DB
}

func NewAIModelRepository(db *gorm.DB) domain.AIModelRepository {
	return &GormAIModelRepository{db: db}
}

func (r *GormAIModelRepository) GetActive(ctx context.Context) ([]domain.AIModel, error) {
	var models []domain.AIModel
	if err := r.db.WithContext(ctx).Where("is_active = ?", true).Order("priority ASC").Find(&models).Error; err != nil {
		logger.Error(ctx, "Failed to get active AI models", err)
		return nil, err
	}
	return models, nil
}

func (r *GormAIModelRepository) ListAll(ctx context.Context) ([]domain.AIModel, error) {
	var models []domain.AIModel
	if err := r.db.WithContext(ctx).Order("priority ASC, id ASC").Find(&models).Error; err != nil {
		logger.Error(ctx, "Failed to list all AI models", err)
		return nil, err
	}
	return models, nil
}

func (r *GormAIModelRepository) GetByID(ctx context.Context, id uint64) (*domain.AIModel, error) {
	var model domain.AIModel
	if err := r.db.WithContext(ctx).First(&model, id).Error; err != nil {
		return nil, err
	}
	return &model, nil
}

func (r *GormAIModelRepository) GetByModelID(ctx context.Context, modelID string) (*domain.AIModel, error) {
	var model domain.AIModel
	if err := r.db.WithContext(ctx).Where("model_id = ?", modelID).First(&model).Error; err != nil {
		return nil, err
	}
	return &model, nil
}

