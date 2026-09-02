package domain

import (
	"context"
)


// UserRepository defines interface for user data operations
type UserRepository interface {
	Create(ctx context.Context, user *User) error
	FindByEmail(ctx context.Context, email string) (*User, error)
	FindByID(ctx context.Context, id uint64) (*User, error)
	Update(ctx context.Context, user *User) error
}

// AccountRepository defines interface for account data operations
type AccountRepository interface {
	Create(ctx context.Context, acc *Account) error
	FindByUserID(ctx context.Context, userID uint64) (*Account, error)
	ListByUserID(ctx context.Context, userID uint64) ([]Account, error)
	FindByAccountNumber(ctx context.Context, accountNumber string) (*Account, error)
	FindByID(ctx context.Context, id uint64) (*Account, error)
	Update(ctx context.Context, acc *Account) error
}


// TransactionRepository defines interface for transaction persistence & atomic transfers
type TransactionRepository interface {
	Create(ctx context.Context, tx *Transaction) error
	FindByID(ctx context.Context, id uint64) (*Transaction, error)
	FindByReference(ctx context.Context, ref string) (*Transaction, error)
	ListByAccountID(ctx context.Context, accountID uint64, limit int, offset int, category string) ([]Transaction, error)
	ListByDateRange(ctx context.Context, accountID uint64, start, end string) ([]Transaction, error)
	GetSpendingSummary(ctx context.Context, accountID uint64) (*SpendingSummary, error)
	ExecuteTransfer(ctx context.Context, fromAccID uint64, toAccNum string, amountCents int64, description string, category string) (*Transaction, error)
	ExecuteDeposit(ctx context.Context, accID uint64, amountCents int64, description string, category string) (*Transaction, error)
}

// AuthService defines authentication & profile business operations
type AuthService interface {
	Register(ctx context.Context, req *RegisterRequest) (*AuthResponse, error)
	Login(ctx context.Context, req *LoginRequest) (*AuthResponse, error)
	GetUserByID(ctx context.Context, id uint64) (*User, error)
	UpdateAddress(ctx context.Context, userID uint64, req *UpdateAddressRequest) (*User, error)
	UpdateKYC(ctx context.Context, userID uint64, req *UpdateKYCRequest) (*User, error)
}

// AccountService defines bank account query operations
type AccountService interface {
	GetUserAccount(ctx context.Context, userID uint64) (*AccountDetailResponse, error)
	ListUserAccounts(ctx context.Context, userID uint64) (*UserAccountsResponse, error)
	CreateAccount(ctx context.Context, userID uint64, req *CreateAccountRequest) (*Account, error)
	LookupAccount(ctx context.Context, accountNumber string) (map[string]interface{}, error)
	UpdateStatus(ctx context.Context, userID uint64, req *UpdateAccountStatusRequest) (*Account, error)
	UpdateLimits(ctx context.Context, userID uint64, req *UpdateAccountLimitRequest) (*Account, error)
}


// TransferService defines fund transfer and ledger operations
type TransferService interface {
	Transfer(ctx context.Context, userID uint64, req *TransferRequest) (*Transaction, error)
	Deposit(ctx context.Context, userID uint64, req *DepositWithdrawRequest) (*Transaction, error)
	GetTransactions(ctx context.Context, userID uint64, limit int, offset int, category string) ([]Transaction, error)
	GetTransactionDetail(ctx context.Context, userID uint64, identifier string) (*Transaction, error)
	GetSpendingSummary(ctx context.Context, userID uint64) (*SpendingSummary, error)
	GenerateStatement(ctx context.Context, userID uint64, req *StatementRequest) (*StatementResponse, error)
}


// ForexService defines currency conversion and exchange operations
type ForexService interface {
	Convert(ctx context.Context, req *ForexConvertRequest) (*ForexConvertResponse, error)
}

// LoanService defines loan simulation and mortgage underwriting calculations
type LoanService interface {
	Calculate(ctx context.Context, req *LoanCalculateRequest) (*LoanCalculateResponse, error)
}


