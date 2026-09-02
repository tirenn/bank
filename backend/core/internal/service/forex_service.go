package service

import (
	"context"
	"fmt"
	"math"
	"strings"

	"bank-core/internal/domain"
)

type ForexService struct{}

func NewForexService() domain.ForexService {
	return &ForexService{}
}

// Fixed baseline rates relative to USD (1.00 USD)
var baseRatesToUSD = map[string]float64{
	"USD": 1.00,
	"EUR": 0.92,
	"GBP": 0.79,
	"JPY": 154.20,
	"SGD": 1.34,
	"IDR": 15850.00,
	"CAD": 1.36,
	"AUD": 1.52,
	"CHF": 0.88,
}

func (s *ForexService) Convert(ctx context.Context, req *domain.ForexConvertRequest) (*domain.ForexConvertResponse, error) {
	from := strings.ToUpper(strings.TrimSpace(req.FromCurrency))
	to := strings.ToUpper(strings.TrimSpace(req.ToCurrency))

	fromRate, fromOk := baseRatesToUSD[from]
	toRate, toOk := baseRatesToUSD[to]

	if !fromOk {
		return nil, fmt.Errorf("unsupported source currency: %s", from)
	}
	if !toOk {
		return nil, fmt.Errorf("unsupported target currency: %s", to)
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
