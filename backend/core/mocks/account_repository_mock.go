package mocks

import (
	"context"

	"bank-core/internal/domain"
	"github.com/stretchr/testify/mock"
)


type MockAccountRepository struct {
	mock.Mock
}

func (m *MockAccountRepository) Create(ctx context.Context, acc *domain.Account) error {
	args := m.Called(ctx, acc)
	return args.Error(0)
}

func (m *MockAccountRepository) FindByUserID(ctx context.Context, userID uint64) (*domain.Account, error) {
	args := m.Called(ctx, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Account), args.Error(1)
}

func (m *MockAccountRepository) ListByUserID(ctx context.Context, userID uint64) ([]domain.Account, error) {
	args := m.Called(ctx, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]domain.Account), args.Error(1)
}


func (m *MockAccountRepository) FindByAccountNumber(ctx context.Context, accountNumber string) (*domain.Account, error) {
	args := m.Called(ctx, accountNumber)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Account), args.Error(1)
}

func (m *MockAccountRepository) FindByID(ctx context.Context, id uint64) (*domain.Account, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Account), args.Error(1)
}


func (m *MockAccountRepository) Update(ctx context.Context, acc *domain.Account) error {
	args := m.Called(ctx, acc)
	return args.Error(0)
}

