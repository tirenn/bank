package service_test

import (
	"context"
	"testing"

	"bank-core/internal/domain"
	"bank-core/internal/service"
	"bank-core/mocks"
	"github.com/stretchr/testify/assert"
)

func TestAccountService_ResolveAccountByIdentifier(t *testing.T) {
	ctx := context.Background()
	accountRepo := new(mocks.MockAccountRepository)
	userRepo := new(mocks.MockUserRepository)

	svc := service.NewAccountService(accountRepo, userRepo)

	userAccounts := []domain.Account{
		{
			ID:            1,
			UserID:        1001,
			AccountNumber: "ACC-10029384",
			AccountName:   "Primary Checking",
			CardNumber:    "4532 1234 5678 9012",
			CardBrand:     "VISA",
			BalanceCents:  250000,
			Status:        "ACTIVE",
		},
		{
			ID:            2,
			UserID:        1001,
			AccountNumber: "ACC-88776655",
			AccountName:   "High Yield Savings",
			CardNumber:    "5412 9876 5432 1098",
			CardBrand:     "MASTERCARD",
			BalanceCents:  750000,
			Status:        "ACTIVE",
		},
	}

	accountRepo.On("ListByUserID", ctx, uint64(1001)).Return(userAccounts, nil)

	// 1. Resolve by exact AccountNumber
	acc1, err1 := svc.ResolveAccountByIdentifier(ctx, 1001, "ACC-10029384")
	assert.NoError(t, err1)
	assert.Equal(t, uint64(1), acc1.ID)

	// 2. Resolve by Full CardNumber
	acc2, err2 := svc.ResolveAccountByIdentifier(ctx, 1001, "5412-9876-5432-1098")
	assert.NoError(t, err2)
	assert.Equal(t, uint64(2), acc2.ID)

	// 3. Resolve by Last 4 Digits of Card
	acc3, err3 := svc.ResolveAccountByIdentifier(ctx, 1001, "9012")
	assert.NoError(t, err3)
	assert.Equal(t, uint64(1), acc3.ID)

	// 4. Resolve by Account Nickname
	acc4, err4 := svc.ResolveAccountByIdentifier(ctx, 1001, "High Yield Savings")
	assert.NoError(t, err4)
	assert.Equal(t, uint64(2), acc4.ID)

	// 5. Non-existent account
	_, err5 := svc.ResolveAccountByIdentifier(ctx, 1001, "ACC-99999999")
	assert.Error(t, err5)
	assert.Contains(t, err5.Error(), "does not belong to your profile")
}
