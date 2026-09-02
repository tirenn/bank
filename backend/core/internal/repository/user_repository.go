package repository

import (
	"context"
	"errors"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
	"gorm.io/gorm"
)


type GormUserRepository struct {
	db *gorm.DB
}

func NewUserRepository(db *gorm.DB) domain.UserRepository {
	return &GormUserRepository{db: db}
}

func (r *GormUserRepository) Create(ctx context.Context, user *domain.User) error {
	if err := r.db.WithContext(ctx).Create(user).Error; err != nil {
		logger.Error(ctx, "Failed to create user in database", err, map[string]interface{}{"email": user.Email})
		return err
	}
	return nil
}

func (r *GormUserRepository) FindByEmail(ctx context.Context, email string) (*domain.User, error) {
	var user domain.User
	err := r.db.WithContext(ctx).Where("email = ?", email).First(&user).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		logger.Error(ctx, "Error finding user by email", err, map[string]interface{}{"email": email})
		return nil, err
	}
	return &user, nil
}

func (r *GormUserRepository) FindByID(ctx context.Context, id uint64) (*domain.User, error) {
	var user domain.User
	err := r.db.WithContext(ctx).Where("id = ?", id).First(&user).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		logger.Error(ctx, "Error finding user by ID", err, map[string]interface{}{"user_id": id})
		return nil, err
	}
	return &user, nil
}

func (r *GormUserRepository) Update(ctx context.Context, user *domain.User) error {
	if err := r.db.WithContext(ctx).Save(user).Error; err != nil {
		logger.Error(ctx, "Failed to update user in database", err, map[string]interface{}{"user_id": user.ID})
		return err
	}
	return nil
}


