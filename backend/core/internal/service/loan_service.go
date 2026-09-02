package service

import (
	"context"
	"math"

	"bank-core/internal/domain"
)

type LoanService struct{}

func NewLoanService() domain.LoanService {
	return &LoanService{}
}

func (s *LoanService) Calculate(ctx context.Context, req *domain.LoanCalculateRequest) (*domain.LoanCalculateResponse, error) {
	principal := req.PrincipalAmount
	annualRate := req.AnnualRatePct
	termMonths := req.TermMonths
	loanType := req.LoanType
	if loanType == "" {
		loanType = "PERSONAL"
	}

	monthlyRate := (annualRate / 100.0) / 12.0
	var monthlyPayment float64

	if monthlyRate > 0 {
		// M = P * [ i(1 + i)^n ] / [ (1 + i)^n - 1 ]
		numerator := monthlyRate * math.Pow(1.0+monthlyRate, float64(termMonths))
		denominator := math.Pow(1.0+monthlyRate, float64(termMonths)) - 1.0
		monthlyPayment = principal * (numerator / denominator)
	} else {
		monthlyPayment = principal / float64(termMonths)
	}

	totalPayment := monthlyPayment * float64(termMonths)
	totalInterest := totalPayment - principal
	originationFee := principal * 0.01 // 1% underwriting fee

	return &domain.LoanCalculateResponse{
		PrincipalAmount:      principal,
		AnnualRatePct:        annualRate,
		TermMonths:           termMonths,
		LoanType:             loanType,
		MonthlyPayment:       math.Round(monthlyPayment*100) / 100,
		TotalPayment:         math.Round(totalPayment*100) / 100,
		TotalInterest:        math.Round(totalInterest*100) / 100,
		EstimatedOrigination: math.Round(originationFee*100) / 100,
	}, nil
}
