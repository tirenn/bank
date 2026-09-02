package service

import (
	"context"
	"fmt"
	"math"
	"strings"

	"bank-core/internal/domain"
)

// ForexService implements domain.ForexService using domain.ForexRateProvider.
type ForexService struct {
	rateProvider domain.ForexRateProvider
}

// NewForexService initializes Forex usecase with an injected rate provider.
func NewForexService(rateProvider domain.ForexRateProvider) domain.ForexService {
	return &ForexService{
		rateProvider: rateProvider,
	}
}

func (s *ForexService) Convert(ctx context.Context, req *domain.ForexConvertRequest) (*domain.ForexConvertResponse, error) {
	from := strings.ToUpper(strings.TrimSpace(req.FromCurrency))
	to := strings.ToUpper(strings.TrimSpace(req.ToCurrency))

	if from == "" || to == "" {
		return nil, fmt.Errorf("both from and to currency codes are required")
	}

	if req.Amount <= 0 {
		return nil, fmt.Errorf("conversion amount must be greater than zero")
	}

	rates, err := s.rateProvider.GetRates(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to retrieve exchange rates: %w", err)
	}

	fromRate, fromOk := rates[from]
	toRate, toOk := rates[to]

	if !fromOk {
		return nil, fmt.Errorf("unsupported source currency: %s", from)
	}
	if !toOk {
		return nil, fmt.Errorf("unsupported target currency: %s", to)
	}

	if fromRate <= 0 {
		fromRate = 1.0
	}

	// 1 unit of from in USD = 1 / fromRate
	// 1 unit of from in to = (1 / fromRate) * toRate = toRate / fromRate
	exchangeRate := toRate / fromRate
	spreadFeePct := 0.25 // 0.25% institutional spread
	feeUSD := (req.Amount / fromRate) * (spreadFeePct / 100.0)

	convertedAmount := req.Amount * exchangeRate

	return &domain.ForexConvertResponse{
		FromCurrency:    from,
		ToCurrency:      to,
		OriginalAmount:  req.Amount,
		ConvertedAmount: math.Round(convertedAmount*100) / 100,
		ExchangeRate:    math.Round(exchangeRate*10000) / 10000,
		SpreadFeePct:    spreadFeePct,
		EstimatedFeeUSD: math.Round(feeUSD*100) / 100,
	}, nil
}
