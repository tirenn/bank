package domain

import (
	"context"
	"time"
)

type AIModel struct {
	ID        uint64    `gorm:"primaryKey;autoIncrement" json:"id"`
	Name      string    `gorm:"type:varchar(255);not null" json:"name"`
	ModelID   string    `gorm:"type:varchar(255);unique;not null" json:"model_id"`
	Provider  string    `gorm:"type:varchar(100);not null;default:'openrouter'" json:"provider"`
	IsFree    bool      `gorm:"not null;default:true" json:"is_free"`
	IsActive  bool      `gorm:"not null;default:true" json:"is_active"`
	Priority  int       `gorm:"not null;default:1" json:"priority"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

func (AIModel) TableName() string {
	return "ai_models"
}

type AIModelResponse struct {
	Models       []string `json:"models"`
	DefaultModel string   `json:"default_model"`
	Details      []AIModel `json:"details"`
}

type AIModelRepository interface {
	GetActive(ctx context.Context) ([]AIModel, error)
	ListAll(ctx context.Context) ([]AIModel, error)
	GetByID(ctx context.Context, id uint64) (*AIModel, error)
	GetByModelID(ctx context.Context, modelID string) (*AIModel, error)
}

type AIModelService interface {
	GetActiveModels(ctx context.Context) (*AIModelResponse, error)
	ListAllModels(ctx context.Context) ([]AIModel, error)
}

