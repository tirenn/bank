package domain

type ForexConvertRequest struct {
	FromCurrency string  `json:"from" binding:"required"`
	ToCurrency   string  `json:"to" binding:"required"`
	Amount       float64 `json:"amount" binding:"required,gt=0"`
}

type ForexConvertResponse struct {
	FromCurrency    string  `json:"from"`
	ToCurrency      string  `json:"to"`
	OriginalAmount  float64 `json:"original_amount"`
	ConvertedAmount float64 `json:"converted_amount"`
	ExchangeRate    float64 `json:"exchange_rate"`
	SpreadFeePct    float64 `json:"spread_fee_pct"`
	EstimatedFeeUSD float64 `json:"estimated_fee_usd"`
}
