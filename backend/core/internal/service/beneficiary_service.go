package service

import (
	"context"
	"errors"
	"time"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
)

type BeneficiaryService struct {
	repo domain.BeneficiaryRepository
}

func NewBeneficiaryService(repo domain.BeneficiaryRepository) domain.BeneficiaryService {
	return &BeneficiaryService{repo: repo}
}

func (s *BeneficiaryService) AddBeneficiary(ctx context.Context, userID uint64, req *domain.AddBeneficiaryRequest) (*domain.Beneficiary, error) {
	if req.Nickname == "" || req.AccountNumber == "" {
		return nil, errors.New("nickname and account number are required")
	}

	bankName := req.BankName
	if bankName == "" {
		bankName = "Tirenn Core Bank"
	}

	b := &domain.Beneficiary{
		UserID:        userID,
		Nickname:      req.Nickname,
		AccountNumber: req.AccountNumber,
		BankName:      bankName,
		CreatedAt:     time.Now(),
	}

	if err := s.repo.Create(ctx, b); err != nil {
		return nil, err
	}

	logger.Info(ctx, "Beneficiary saved successfully", map[string]interface{}{
		"user_id":        userID,
		"nickname":       req.Nickname,
		"account_number": req.AccountNumber,
	})

	return b, nil
}

func (s *BeneficiaryService) GetBeneficiaries(ctx context.Context, userID uint64) ([]domain.Beneficiary, error) {
	return s.repo.ListByUserID(ctx, userID)
}

func (s *BeneficiaryService) DeleteBeneficiary(ctx context.Context, userID, id uint64) error {
	return s.repo.Delete(ctx, userID, id)
}
