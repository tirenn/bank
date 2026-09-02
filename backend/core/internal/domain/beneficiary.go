package domain

import (
	"context"
	"time"
)


type Beneficiary struct {
	ID            uint64    `gorm:"primaryKey;autoIncrement" json:"id"`
	UserID        uint64    `gorm:"not null;index" json:"user_id"`
	Nickname      string    `gorm:"type:varchar(100);not null" json:"nickname"`
	AccountNumber string    `gorm:"type:varchar(32);not null" json:"account_number"`
	BankName      string    `gorm:"type:varchar(100);not null" json:"bank_name"`
	CreatedAt     time.Time `json:"created_at"`
}

func (Beneficiary) TableName() string {
	return "beneficiaries"
}

type AddBeneficiaryRequest struct {
	Nickname      string `json:"nickname" binding:"required"`
	AccountNumber string `json:"account_number" binding:"required"`
	BankName      string `json:"bank_name"`
}

type BeneficiaryRepository interface {
	Create(ctx context.Context, b *Beneficiary) error
	ListByUserID(ctx context.Context, userID uint64) ([]Beneficiary, error)
	Delete(ctx context.Context, userID, id uint64) error
}

type BeneficiaryService interface {
	AddBeneficiary(ctx context.Context, userID uint64, req *AddBeneficiaryRequest) (*Beneficiary, error)
	GetBeneficiaries(ctx context.Context, userID uint64) ([]Beneficiary, error)
	DeleteBeneficiary(ctx context.Context, userID, id uint64) error
}

