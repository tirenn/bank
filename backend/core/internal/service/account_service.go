package service

import (
	"context"
	"crypto/rand"
	"errors"
	"fmt"
	"math/big"
	"strings"
	"time"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
)

type AccountService struct {
	accountRepo domain.AccountRepository
	userRepo    domain.UserRepository
}

func NewAccountService(accountRepo domain.AccountRepository, userRepo domain.UserRepository) domain.AccountService {
	return &AccountService{
		accountRepo: accountRepo,
		userRepo:    userRepo,
	}
}

func (s *AccountService) GetUserAccount(ctx context.Context, userID uint64) (*domain.AccountDetailResponse, error) {
	acc, err := s.accountRepo.FindByUserID(ctx, userID)
	if err != nil {
		logger.Error(ctx, "Error fetching user account", err, map[string]interface{}{"user_id": userID})
		return nil, err
	}
	if acc == nil {
		return nil, errors.New("no bank account found for this user")
	}

	user, err := s.userRepo.FindByID(ctx, userID)
	if err != nil {
		logger.Error(ctx, "Error fetching user profile", err, map[string]interface{}{"user_id": userID})
		return nil, err
	}
	if user == nil {
		return nil, errors.New("user not found")
	}

	return &domain.AccountDetailResponse{
		Account: *acc,
		User:    *user,
	}, nil
}

func (s *AccountService) ListUserAccounts(ctx context.Context, userID uint64) (*domain.UserAccountsResponse, error) {
	accounts, err := s.accountRepo.ListByUserID(ctx, userID)
	if err != nil {
		logger.Error(ctx, "Error listing user accounts", err, map[string]interface{}{"user_id": userID})
		return nil, err
	}

	user, err := s.userRepo.FindByID(ctx, userID)
	if err != nil || user == nil {
		return nil, errors.New("user not found")
	}

	return &domain.UserAccountsResponse{
		Accounts: accounts,
		Count:    len(accounts),
		User:     *user,
	}, nil
}

func (s *AccountService) CreateAccount(ctx context.Context, userID uint64, req *domain.CreateAccountRequest) (*domain.Account, error) {
	user, err := s.userRepo.FindByID(ctx, userID)
	if err != nil || user == nil {
		return nil, errors.New("user not found")
	}

	accName := strings.TrimSpace(req.AccountName)
	if accName == "" {
		accName = "Secondary Account"
	}

	accType := strings.ToUpper(strings.TrimSpace(req.AccountType))
	if accType == "" {
		accType = "SAVINGS"
	}

	curr := strings.ToUpper(strings.TrimSpace(req.Currency))
	if curr == "" {
		curr = "USD"
	}

	brand := strings.ToUpper(strings.TrimSpace(req.CardBrand))
	if brand != "MASTERCARD" && brand != "VISA" {
		brand = "VISA"
	}

	// 1. Generate Account Number
	randomNum, _ := rand.Int(rand.Reader, big.NewInt(89999999))
	accNum := fmt.Sprintf("ACC-%08d", randomNum.Int64()+10000000)

	// 2. Generate 16-Digit Card Number
	prefix := "4532" // Visa default
	if brand == "MASTERCARD" {
		prefix = "5412"
	}
	r1, _ := rand.Int(rand.Reader, big.NewInt(9000))
	r2, _ := rand.Int(rand.Reader, big.NewInt(9000))
	r3, _ := rand.Int(rand.Reader, big.NewInt(9000))
	cardNum := fmt.Sprintf("%s %04d %04d %04d", prefix, r1.Int64()+1000, r2.Int64()+1000, r3.Int64()+1000)

	// 3. Generate Expiry (4 years from now) & CVV
	now := time.Now()
	expiry := fmt.Sprintf("%02d/%02d", now.Month(), (now.Year()+4)%100)
	cvvNum, _ := rand.Int(rand.Reader, big.NewInt(900))
	cvv := fmt.Sprintf("%03d", cvvNum.Int64()+100)

	initialDepositCents := int64(req.InitialDepositDollars * 100)
	if initialDepositCents < 0 {
		initialDepositCents = 0
	}

	account := domain.Account{
		UserID:                  userID,
		AccountNumber:           accNum,
		AccountName:             accName,
		AccountType:             accType,
		CardNumber:              cardNum,
		CardBrand:               brand,
		CardExpiry:              expiry,
		CardCVV:                 cvv,
		BalanceCents:            initialDepositCents,
		Currency:                curr,
		Status:                  "ACTIVE",
		DailyTransferLimitCents: 1000000, // $10,000 daily limit
		IsFrozen:                false,
		CreatedAt:               now,
	}

	if err := s.accountRepo.Create(ctx, &account); err != nil {
		logger.Error(ctx, "Failed to create new account", err, map[string]interface{}{"user_id": userID})
		return nil, err
	}

	logger.Info(ctx, "New account created successfully", map[string]interface{}{
		"user_id":        userID,
		"account_number": accNum,
		"account_name":   accName,
		"card_number":    cardNum,
		"card_brand":     brand,
	})

	return &account, nil
}

func (s *AccountService) LookupAccount(ctx context.Context, accountNumber string) (map[string]interface{}, error) {
	acc, err := s.accountRepo.FindByAccountNumber(ctx, accountNumber)
	if err != nil {
		logger.Error(ctx, "Error looking up account", err, map[string]interface{}{"account_number": accountNumber})
		return nil, err
	}
	if acc == nil {
		return nil, errors.New("account number not found")
	}

	user, err := s.userRepo.FindByID(ctx, acc.UserID)
	if err != nil {
		return nil, err
	}
	if user == nil {
		return nil, errors.New("account owner not found")
	}

	return map[string]interface{}{
		"account_number": acc.AccountNumber,
		"account_name":   acc.AccountName,
		"owner_name":     user.FullName,
		"currency":       acc.Currency,
		"status":         acc.Status,
		"card_brand":     acc.CardBrand,
	}, nil
}

func (s *AccountService) UpdateStatus(ctx context.Context, userID uint64, req *domain.UpdateAccountStatusRequest) (*domain.Account, error) {
	var acc *domain.Account
	var err error

	if req.AccountNumber != "" || req.CardNumber != "" {
		accounts, listErr := s.accountRepo.ListByUserID(ctx, userID)
		if listErr != nil {
			return nil, listErr
		}
		cleanTargetCard := strings.ReplaceAll(strings.ReplaceAll(req.CardNumber, " ", ""), "-", "")
		for i := range accounts {
			a := &accounts[i]
			cleanCard := strings.ReplaceAll(strings.ReplaceAll(a.CardNumber, " ", ""), "-", "")
			if req.AccountNumber != "" && strings.EqualFold(a.AccountNumber, strings.TrimSpace(req.AccountNumber)) {
				acc = a
				break
			}
			if cleanTargetCard != "" && (cleanCard == cleanTargetCard || strings.HasSuffix(cleanCard, cleanTargetCard)) {
				acc = a
				break
			}
		}
	} else if req.AccountID > 0 {
		acc, err = s.accountRepo.FindByID(ctx, req.AccountID)
		if err == nil && acc != nil && acc.UserID != userID {
			return nil, errors.New("access denied for this account")
		}
	} else {
		acc, err = s.accountRepo.FindByUserID(ctx, userID)
	}

	if err != nil {
		return nil, err
	}
	if acc == nil {
		return nil, errors.New("account not found")
	}

	acc.IsFrozen = req.Frozen
	if req.Frozen {
		acc.Status = "FROZEN"
	} else {
		acc.Status = "ACTIVE"
	}

	if err := s.accountRepo.Update(ctx, acc); err != nil {
		return nil, err
	}

	logger.Info(ctx, "Account freeze status updated", map[string]interface{}{
		"user_id":        userID,
		"account_number": acc.AccountNumber,
		"is_frozen":      acc.IsFrozen,
		"status":         acc.Status,
	})

	return acc, nil
}

func (s *AccountService) UpdateLimits(ctx context.Context, userID uint64, req *domain.UpdateAccountLimitRequest) (*domain.Account, error) {
	var acc *domain.Account
	var err error

	if req.AccountNumber != "" || req.CardNumber != "" {
		accounts, listErr := s.accountRepo.ListByUserID(ctx, userID)
		if listErr != nil {
			return nil, listErr
		}
		cleanTargetCard := strings.ReplaceAll(strings.ReplaceAll(req.CardNumber, " ", ""), "-", "")
		for i := range accounts {
			a := &accounts[i]
			cleanCard := strings.ReplaceAll(strings.ReplaceAll(a.CardNumber, " ", ""), "-", "")
			if req.AccountNumber != "" && strings.EqualFold(a.AccountNumber, strings.TrimSpace(req.AccountNumber)) {
				acc = a
				break
			}
			if cleanTargetCard != "" && (cleanCard == cleanTargetCard || strings.HasSuffix(cleanCard, cleanTargetCard)) {
				acc = a
				break
			}
		}
	} else if req.AccountID > 0 {
		acc, err = s.accountRepo.FindByID(ctx, req.AccountID)
		if err == nil && acc != nil && acc.UserID != userID {
			return nil, errors.New("access denied for this account")
		}
	} else {
		acc, err = s.accountRepo.FindByUserID(ctx, userID)
	}

	if err != nil {
		return nil, err
	}
	if acc == nil {
		return nil, errors.New("account not found")
	}

	acc.DailyTransferLimitCents = req.DailyTransferLimitCents

	if err := s.accountRepo.Update(ctx, acc); err != nil {
		return nil, err
	}

	logger.Info(ctx, "Account transfer limits updated", map[string]interface{}{
		"user_id":        userID,
		"account_number": acc.AccountNumber,
		"limit":          req.DailyTransferLimitCents,
	})

	return acc, nil
}




