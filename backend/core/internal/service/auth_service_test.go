package service_test

import (
	"context"
	"testing"

	"bank-core/internal/domain"
	"bank-core/internal/service"
	"bank-core/mocks"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"golang.org/x/crypto/bcrypt"
)

func TestAuthService_Register_Success(t *testing.T) {
	ctx := context.Background()
	userRepo := new(mocks.MockUserRepository)
	accountRepo := new(mocks.MockAccountRepository)
	jwtSecret := "test-secret"

	authSvc := service.NewAuthService(userRepo, accountRepo, jwtSecret)

	req := &domain.RegisterRequest{
		Email:    "newuser@bank.com",
		Password: "securepassword123",
		FullName: "New User",
	}

	userRepo.On("FindByEmail", ctx, req.Email).Return(nil, nil)
	userRepo.On("Create", ctx, mock.AnythingOfType("*domain.User")).Return(nil)
	accountRepo.On("Create", ctx, mock.AnythingOfType("*domain.Account")).Return(nil)

	res, err := authSvc.Register(ctx, req)

	assert.NoError(t, err)
	assert.NotNil(t, res)
	assert.NotEmpty(t, res.Token)
	assert.Equal(t, req.Email, res.User.Email)
	assert.Equal(t, req.FullName, res.User.FullName)

	userRepo.AssertExpectations(t)
	accountRepo.AssertExpectations(t)
}

func TestAuthService_Login_Success(t *testing.T) {
	ctx := context.Background()
	userRepo := new(mocks.MockUserRepository)
	accountRepo := new(mocks.MockAccountRepository)
	jwtSecret := "test-secret"

	authSvc := service.NewAuthService(userRepo, accountRepo, jwtSecret)

	hashedPassword, _ := bcrypt.GenerateFromPassword([]byte("password123"), bcrypt.DefaultCost)
	existingUser := &domain.User{
		Email:        "existing@bank.com",
		PasswordHash: string(hashedPassword),
		FullName:     "Existing User",
	}

	userRepo.On("FindByEmail", ctx, "existing@bank.com").Return(existingUser, nil)

	req := &domain.LoginRequest{
		Email:    "existing@bank.com",
		Password: "password123",
	}

	res, err := authSvc.Login(ctx, req)

	assert.NoError(t, err)
	assert.NotNil(t, res)
	assert.NotEmpty(t, res.Token)
	assert.Equal(t, "existing@bank.com", res.User.Email)

	userRepo.AssertExpectations(t)
}
