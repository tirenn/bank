package domain

import (
	"time"
)


type Account struct {
	ID                     uint64    `gorm:"primaryKey;autoIncrement" json:"id"`
	UserID                 uint64    `gorm:"not null;index" json:"user_id"`
	AccountNumber          string    `gorm:"uniqueIndex;type:varchar(32);not null" json:"account_number"`
	AccountName            string    `gorm:"type:varchar(100)" json:"account_name"`
	AccountType            string    `gorm:"type:varchar(32)" json:"account_type"`
	CardNumber             string    `gorm:"type:varchar(32)" json:"card_number"`
	CardBrand              string    `gorm:"type:varchar(32)" json:"card_brand"`
	CardExpiry             string    `gorm:"type:varchar(10)" json:"card_expiry"`
	CardCVV                string    `gorm:"type:varchar(4)" json:"card_cvv"`
	BalanceCents           int64     `gorm:"type:bigint;not null" json:"balance_cents"`
	Currency               string    `gorm:"type:varchar(3);not null" json:"currency"`
	Status                 string    `gorm:"type:varchar(16);not null" json:"status"`
	DailyTransferLimitCents int64    `gorm:"type:bigint" json:"daily_transfer_limit_cents"`
	IsFrozen               bool      `json:"is_frozen"`
	CreatedAt              time.Time `json:"created_at"`
}

func (Account) TableName() string {
	return "accounts"
}

type AccountDetailResponse struct {
	Account Account `json:"account"`
	User    User    `json:"user"`
}

type UserAccountsResponse struct {
	Accounts []Account `json:"accounts"`
	Count    int       `json:"count"`
	User     User      `json:"user"`
}

type CreateAccountRequest struct {
	AccountName         string  `json:"account_name" binding:"required"`
	AccountType         string  `json:"account_type"`
	Currency            string  `json:"currency"`
	CardBrand           string  `json:"card_brand"`
	InitialDepositDollars float64 `json:"initial_deposit_dollars"`
}

type UpdateAccountStatusRequest struct {
	AccountID uint64 `json:"account_id,omitempty"`
	Frozen    bool   `json:"frozen"`
	Reason    string `json:"reason"`
}

type UpdateAccountLimitRequest struct {
	AccountID               uint64 `json:"account_id,omitempty"`
	DailyTransferLimitCents int64  `json:"daily_transfer_limit_cents"`
}



