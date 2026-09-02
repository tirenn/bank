package domain

type LoanCalculateRequest struct {
	PrincipalAmount float64 `json:"principal" binding:"required,gt=0"`
	AnnualRatePct   float64 `json:"annual_rate_pct" binding:"required,gt=0"`
	TermMonths      int     `json:"term_months" binding:"required,gt=0"`
	LoanType        string  `json:"loan_type"` // e.g. "PERSONAL", "MORTGAGE", "AUTO"
}

type LoanCalculateResponse struct {
	PrincipalAmount      float64 `json:"principal"`
	AnnualRatePct        float64 `json:"annual_rate_pct"`
	TermMonths           int     `json:"term_months"`
	LoanType             string  `json:"loan_type"`
	MonthlyPayment       float64 `json:"monthly_payment"`
	TotalPayment         float64 `json:"total_payment"`
	TotalInterest        float64 `json:"total_interest"`
	EstimatedOrigination float64 `json:"estimated_origination_fee"`
}
