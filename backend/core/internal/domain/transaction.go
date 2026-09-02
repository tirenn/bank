package domain

import (
	"time"
)


type TransactionType string

const (
	TransactionDeposit     TransactionType = "DEPOSIT"
	TransactionWithdrawal  TransactionType = "WITHDRAWAL"
	TransactionTransferIn  TransactionType = "TRANSFER_IN"
	TransactionTransferOut TransactionType = "TRANSFER_OUT"
)

type Transaction struct {
	ID                     uint64          `gorm:"primaryKey;autoIncrement" json:"id"`
	AccountID              uint64          `gorm:"not null;index" json:"account_id"`
	Type                   TransactionType `gorm:"type:varchar(32);not null" json:"type"`
	AmountCents            int64           `gorm:"type:bigint;not null" json:"amount_cents"`
	Description            string          `gorm:"type:text" json:"description"`
	Category               string          `gorm:"type:varchar(64)" json:"category"`
	CounterpartyAccountNum string          `gorm:"type:varchar(32)" json:"counterparty_account_num,omitempty"`
	CounterpartyName       string          `gorm:"type:varchar(255)" json:"counterparty_name,omitempty"`
	ReferenceNumber        string          `gorm:"uniqueIndex;type:varchar(64);not null" json:"reference_number"`
	CreatedAt              time.Time       `gorm:"index" json:"created_at"`
}

func (Transaction) TableName() string {
	return "transactions"
}

type TransferRequest struct {
	FromAccountID    *uint64 `json:"from_account_id,omitempty"`
	ToAccountNumber  string  `json:"to_account_number" binding:"required"`
	AmountCents      int64   `json:"amount_cents" binding:"required,gt=0"`
	Description      string  `json:"description"`
	Category         string  `json:"category"`
}

type DepositWithdrawRequest struct {
	AccountID   *uint64 `json:"account_id,omitempty"`
	AmountCents int64   `json:"amount_cents" binding:"required,gt=0"`
	Description string  `json:"description"`
	Category    string  `json:"category"`
}


type SpendingSummary struct {
	TotalIncomeCents   int64            `json:"total_income_cents"`
	TotalSpendingCents int64            `json:"total_spending_cents"`
	CategoryBreakdown  map[string]int64 `json:"category_breakdown"`
	TransactionCount   int              `json:"transaction_count"`
}

type StatementRequest struct {
	StartDate *time.Time `json:"start_date"`
	EndDate   *time.Time `json:"end_date"`
	Month     int        `json:"month,omitempty"`
	Year      int        `json:"year,omitempty"`
}

type StatementResponse struct {
	StatementID         string        `json:"statement_id"`
	AccountNumber       string        `json:"account_number"`
	AccountHolder       string        `json:"account_holder"`
	PeriodStart         time.Time     `json:"period_start"`
	PeriodEnd           time.Time     `json:"period_end"`
	StartingBalanceCents int64        `json:"starting_balance_cents"`
	EndingBalanceCents   int64        `json:"ending_balance_cents"`
	TotalDepositsCents   int64        `json:"total_deposits_cents"`
	TotalWithdrawalsCents int64       `json:"total_withdrawals_cents"`
	TransactionCount    int           `json:"transaction_count"`
	Transactions        []Transaction `json:"transactions"`
	GeneratedAt         time.Time     `json:"generated_at"`
}

