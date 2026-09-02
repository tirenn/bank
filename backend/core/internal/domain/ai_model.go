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

type CreateAIModelRequest struct {
	Name     string `json:"name" binding:"required"`
	ModelID  string `json:"model_id" binding:"required"`
	Provider string `json:"provider"`
	IsFree   bool   `json:"is_free"`
	IsActive bool   `json:"is_active"`
	Priority int    `json:"priority"`
}

type UpdateAIModelRequest struct {
	Name     *string `json:"name"`
	Provider *string `json:"provider"`
	IsFree   *bool   `json:"is_free"`
	IsActive *bool   `json:"is_active"`
	Priority *int    `json:"priority"`
}

type AIModelRepository interface {
	GetActive(ctx context.Context) ([]AIModel, error)
	ListAll(ctx context.Context) ([]AIModel, error)
	GetByID(ctx context.Context, id uint64) (*AIModel, error)
	GetByModelID(ctx context.Context, modelID string) (*AIModel, error)
	Create(ctx context.Context, m *AIModel) error
	Update(ctx context.Context, m *AIModel) error
	Delete(ctx context.Context, id uint64) error
}

type AIModelService interface {
	GetActiveModels(ctx context.Context) (*AIModelResponse, error)
	ListAllModels(ctx context.Context) ([]AIModel, error)
	CreateModel(ctx context.Context, req *CreateAIModelRequest) (*AIModel, error)
	UpdateModel(ctx context.Context, id uint64, req *UpdateAIModelRequest) (*AIModel, error)
	DeleteModel(ctx context.Context, id uint64) error
}
