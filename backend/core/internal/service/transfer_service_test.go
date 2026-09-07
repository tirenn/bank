package service_test

import (
	"context"
	"errors"
	"testing"

	"bank-core/internal/domain"
	"bank-core/internal/service"
	"bank-core/mocks"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type MockTransactionRepository struct {
	mock.Mock
}

func (m *MockTransactionRepository) Create(ctx context.Context, tx *domain.Transaction) error {
	args := m.Called(ctx, tx)
	return args.Error(0)
}

func (m *MockTransactionRepository) FindByID(ctx context.Context, id uint64) (*domain.Transaction, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func (m *MockTransactionRepository) FindByReference(ctx context.Context, ref string) (*domain.Transaction, error) {
	args := m.Called(ctx, ref)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func (m *MockTransactionRepository) ListByAccountID(ctx context.Context, accID uint64, limit int, offset int, category string) ([]domain.Transaction, error) {
	args := m.Called(ctx, accID, limit, offset, category)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]domain.Transaction), args.Error(1)
}

func (m *MockTransactionRepository) ListByDateRange(ctx context.Context, accountID uint64, start, end string) ([]domain.Transaction, error) {
	args := m.Called(ctx, accountID, start, end)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]domain.Transaction), args.Error(1)
}

func (m *MockTransactionRepository) GetSpendingSummary(ctx context.Context, accID uint64) (*domain.SpendingSummary, error) {
	args := m.Called(ctx, accID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.SpendingSummary), args.Error(1)
}

func (m *MockTransactionRepository) ExecuteTransfer(ctx context.Context, fromAccID uint64, toAccNum string, amountCents int64, description string, category string) (*domain.Transaction, error) {
	args := m.Called(ctx, fromAccID, toAccNum, amountCents, description, category)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func (m *MockTransactionRepository) ExecuteDeposit(ctx context.Context, accID uint64, amountCents int64, description string, category string) (*domain.Transaction, error) {
	args := m.Called(ctx, accID, amountCents, description, category)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func TestTransferService_DraftTransfer_ZeroOrNegativeAmount(t *testing.T) {
	ctx := context.Background()
	txRepo := new(MockTransactionRepository)
	accountRepo := new(mocks.MockAccountRepository)
	userRepo := new(mocks.MockUserRepository)

	svc := service.NewTransferService(txRepo, accountRepo, userRepo, "123456")

	_, err := svc.DraftTransfer(ctx, 1001, &domain.DraftTransferRequest{
		ToAccountNumber: "ACC-99998888",
		AmountDollars:   0,
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "strictly greater than zero")

	_, errNeg := svc.DraftTransfer(ctx, 1001, &domain.DraftTransferRequest{
		ToAccountNumber: "ACC-99998888",
		AmountDollars:   -10.0,
	})
	assert.Error(t, errNeg)
	assert.Contains(t, errNeg.Error(), "strictly greater than zero")
}

func TestTransferService_DraftTransfer_MissingRecipient(t *testing.T) {
	ctx := context.Background()
	txRepo := new(MockTransactionRepository)
	accountRepo := new(mocks.MockAccountRepository)
	userRepo := new(mocks.MockUserRepository)

	svc := service.NewTransferService(txRepo, accountRepo, userRepo, "123456")

	_, err := svc.DraftTransfer(ctx, 1001, &domain.DraftTransferRequest{
		ToAccountNumber: "",
		AmountDollars:   50.0,
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "recipient account number is required")
}

func TestTransferService_DraftTransfer_SourceAccountFrozen(t *testing.T) {
	ctx := context.Background()
	txRepo := new(MockTransactionRepository)
	accountRepo := new(mocks.MockAccountRepository)
	userRepo := new(mocks.MockUserRepository)

	svc := service.NewTransferService(txRepo, accountRepo, userRepo, "123456")

	accountRepo.On("ListByUserID", ctx, uint64(1001)).Return([]domain.Account{
		{
			ID:            10,
			AccountNumber: "ACC-10001111",
			Status:        "FROZEN",
			IsFrozen:      true,
			BalanceCents:  100000,
		},
	}, nil)

	_, err := svc.DraftTransfer(ctx, 1001, &domain.DraftTransferRequest{
		ToAccountNumber: "ACC-99998888",
		AmountDollars:   50.0,
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "cannot be initiated")
}

func TestTransferService_DraftTransfer_SameAccount(t *testing.T) {
	ctx := context.Background()
	txRepo := new(MockTransactionRepository)
	accountRepo := new(mocks.MockAccountRepository)
	userRepo := new(mocks.MockUserRepository)

	svc := service.NewTransferService(txRepo, accountRepo, userRepo, "123456")

	accountRepo.On("ListByUserID", ctx, uint64(1001)).Return([]domain.Account{
		{
			ID:            10,
			AccountNumber: "ACC-10001111",
			Status:        "ACTIVE",
			BalanceCents:  100000,
		},
	}, nil)

	_, err := svc.DraftTransfer(ctx, 1001, &domain.DraftTransferRequest{
		ToAccountNumber: "ACC-10001111",
		AmountDollars:   50.0,
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "cannot transfer funds to the same source account")
}

func TestTransferService_DraftTransfer_InsufficientFunds(t *testing.T) {
	ctx := context.Background()
	txRepo := new(MockTransactionRepository)
	accountRepo := new(mocks.MockAccountRepository)
	userRepo := new(mocks.MockUserRepository)

	svc := service.NewTransferService(txRepo, accountRepo, userRepo, "123456")

	accountRepo.On("ListByUserID", ctx, uint64(1001)).Return([]domain.Account{
		{
			ID:            10,
			AccountNumber: "ACC-10001111",
			Status:        "ACTIVE",
			BalanceCents:  2500, // $25.00
		},
	}, nil)

	_, err := svc.DraftTransfer(ctx, 1001, &domain.DraftTransferRequest{
		ToAccountNumber: "ACC-99998888",
		AmountDollars:   50.0,
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "insufficient funds in account ACC-10001111")
}

func TestTransferService_DraftTransfer_ExceedsDailyLimit(t *testing.T) {
	ctx := context.Background()
	txRepo := new(MockTransactionRepository)
	accountRepo := new(mocks.MockAccountRepository)
	userRepo := new(mocks.MockUserRepository)

	svc := service.NewTransferService(txRepo, accountRepo, userRepo, "123456")

	accountRepo.On("ListByUserID", ctx, uint64(1001)).Return([]domain.Account{
		{
			ID:                      10,
			AccountNumber:           "ACC-10001111",
			Status:                  "ACTIVE",
			BalanceCents:            1000000, // $10,000
			DailyTransferLimitCents: 50000,   // $500 limit
		},
	}, nil)

	_, err := svc.DraftTransfer(ctx, 1001, &domain.DraftTransferRequest{
		ToAccountNumber: "ACC-99998888",
		AmountDollars:   600.0, // $600 exceeds limit
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "exceeds daily transfer limit")
}

func TestTransferService_DraftTransfer_RecipientNotFound(t *testing.T) {
	ctx := context.Background()
	txRepo := new(MockTransactionRepository)
	accountRepo := new(mocks.MockAccountRepository)
	userRepo := new(mocks.MockUserRepository)

	svc := service.NewTransferService(txRepo, accountRepo, userRepo, "123456")

	accountRepo.On("ListByUserID", ctx, uint64(1001)).Return([]domain.Account{
		{
			ID:            10,
			AccountNumber: "ACC-10001111",
			Status:        "ACTIVE",
			BalanceCents:  100000,
		},
	}, nil)

	accountRepo.On("FindByAccountNumber", ctx, "ACC-NONEXISTENT").Return(nil, errors.New("not found"))

	_, err := svc.DraftTransfer(ctx, 1001, &domain.DraftTransferRequest{
		ToAccountNumber: "ACC-NONEXISTENT",
		AmountDollars:   50.0,
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "was not found or does not exist")
}

func TestTransferService_DraftTransfer_RecipientFrozen(t *testing.T) {
	ctx := context.Background()
	txRepo := new(MockTransactionRepository)
	accountRepo := new(mocks.MockAccountRepository)
	userRepo := new(mocks.MockUserRepository)

	svc := service.NewTransferService(txRepo, accountRepo, userRepo, "123456")

	accountRepo.On("ListByUserID", ctx, uint64(1001)).Return([]domain.Account{
		{
			ID:            10,
			AccountNumber: "ACC-10001111",
			Status:        "ACTIVE",
			BalanceCents:  100000,
		},
	}, nil)

	accountRepo.On("FindByAccountNumber", ctx, "ACC-99998888").Return(&domain.Account{
		ID:            20,
		AccountNumber: "ACC-99998888",
		Status:        "FROZEN",
		IsFrozen:      true,
	}, nil)

	_, err := svc.DraftTransfer(ctx, 1001, &domain.DraftTransferRequest{
		ToAccountNumber: "ACC-99998888",
		AmountDollars:   50.0,
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "is not active")
}

func TestTransferService_DraftTransfer_Success(t *testing.T) {
	ctx := context.Background()
	txRepo := new(MockTransactionRepository)
	accountRepo := new(mocks.MockAccountRepository)
	userRepo := new(mocks.MockUserRepository)

	svc := service.NewTransferService(txRepo, accountRepo, userRepo, "123456")

	accountRepo.On("ListByUserID", ctx, uint64(1001)).Return([]domain.Account{
		{
			ID:            10,
			AccountNumber: "ACC-10001111",
			Status:        "ACTIVE",
			BalanceCents:  100000, // $1,000.00
		},
	}, nil)

	accountRepo.On("FindByAccountNumber", ctx, "ACC-99998888").Return(&domain.Account{
		ID:            20,
		UserID:        2002,
		AccountNumber: "ACC-99998888",
		Status:        "ACTIVE",
	}, nil)

	userRepo.On("FindByID", ctx, uint64(2002)).Return(&domain.User{
		ID:       2002,
		FullName: "Charlie Recipient",
	}, nil)

	draft, err := svc.DraftTransfer(ctx, 1001, &domain.DraftTransferRequest{
		ToAccountNumber: "ACC-99998888",
		AmountDollars:   125.00,
		Description:     "Project bonus",
		Category:        "Salary",
	})

	assert.NoError(t, err)
	assert.NotNil(t, draft)
	assert.Equal(t, uint64(10), draft.FromAccountID)
	assert.Equal(t, "ACC-10001111", draft.FromAccountNumber)
	assert.Equal(t, "ACC-99998888", draft.ToAccountNumber)
	assert.Equal(t, "Charlie Recipient", draft.RecipientName)
	assert.Equal(t, 125.00, draft.AmountDollars)
	assert.Equal(t, int64(12500), draft.AmountCents)
	assert.Equal(t, "Project bonus", draft.Description)
	assert.Equal(t, "Salary", draft.Category)
	assert.Contains(t, draft.SummaryText, "Transfer Authorization Draft")
}
