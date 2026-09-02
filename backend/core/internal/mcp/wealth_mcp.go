package mcp

import (
	"context"
	"fmt"
	"net/http"

	"bank-core/internal/domain"
	"github.com/gin-gonic/gin"
)


type WealthMCPServer struct {
	forexService       domain.ForexService
	loanService        domain.LoanService
	beneficiaryService domain.BeneficiaryService
}

func NewWealthMCPServer(
	forexService domain.ForexService,
	loanService domain.LoanService,
	beneficiaryService domain.BeneficiaryService,
) *WealthMCPServer {
	return &WealthMCPServer{
		forexService:       forexService,
		loanService:        loanService,
		beneficiaryService: beneficiaryService,
	}
}

func (s *WealthMCPServer) HandleJSONRPC(c *gin.Context) {
	var req JSONRPCRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, JSONRPCResponse{
			JSONRPC: "2.0",
			ID:      nil,
			Error:   &RPCError{Code: -32700, Message: "Parse error"},
		})
		return
	}

	ctx := c.Request.Context()
	userIDVal, hasUser := c.Get("userID")
	var userID uint64
	if hasUser {
		userID = userIDVal.(uint64)
	}


	switch req.Method {
	case "tools/list":
		tools := []ToolDefinition{
			{
				Name:        "calculate_forex_conversion",
				Description: "Calculate live currency exchange rate and institutional spread for USD, EUR, GBP, IDR, SGD, JPY, CAD, AUD, CHF.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"from_currency": map[string]interface{}{"type": "string", "description": "Source currency (e.g. USD)"},
						"to_currency":   map[string]interface{}{"type": "string", "description": "Target currency (e.g. EUR, IDR)"},
						"amount":        map[string]interface{}{"type": "number", "description": "Amount to convert"},
					},
					"required": []string{"from_currency", "to_currency", "amount"},
				},
			},
			{
				Name:        "calculate_loan_mortgage",
				Description: "Simulate monthly installments, interest, and APR for personal loans, auto loans, or home mortgages.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"principal":       map[string]interface{}{"type": "number", "description": "Loan amount in USD"},
						"annual_rate_pct": map[string]interface{}{"type": "number", "description": "Annual rate percentage"},
						"term_months":     map[string]interface{}{"type": "integer", "description": "Duration in months"},
						"loan_type":       map[string]interface{}{"type": "string", "enum": []string{"PERSONAL", "MORTGAGE", "AUTO"}},
					},
					"required": []string{"principal", "annual_rate_pct", "term_months"},
				},
			},
			{
				Name:        "manage_beneficiaries",
				Description: "List saved trusted transfer payees or add a new trusted contact.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"action":         map[string]interface{}{"type": "string", "enum": []string{"list", "add"}},
						"nickname":       map[string]interface{}{"type": "string", "description": "Nickname (required for add)"},
						"account_number": map[string]interface{}{"type": "string", "description": "Account number (required for add)"},
						"bank_name":      map[string]interface{}{"type": "string", "description": "Bank name"},
					},
					"required": []string{"action"},
				},
			},
		}
		c.JSON(http.StatusOK, JSONRPCResponse{
			JSONRPC: "2.0",
			ID:      req.ID,
			Result:  ListToolsResult{Tools: tools},
		})

	case "tools/call":
		toolName, _ := req.Params["name"].(string)
		args, _ := req.Params["arguments"].(map[string]interface{})
		if args == nil {
			args = make(map[string]interface{})
		}

		res := s.executeTool(ctx, userID, toolName, args)
		c.JSON(http.StatusOK, JSONRPCResponse{
			JSONRPC: "2.0",
			ID:      req.ID,
			Result:  res,
		})

	default:
		c.JSON(http.StatusOK, JSONRPCResponse{
			JSONRPC: "2.0",
			ID:      req.ID,
			Error:   &RPCError{Code: -32601, Message: fmt.Sprintf("Method '%s' not found", req.Method)},
		})
	}
}

func (s *WealthMCPServer) executeTool(ctx context.Context, userID uint64, name string, args map[string]interface{}) CallToolResult {

	switch name {
	case "calculate_forex_conversion":
		from := parseString(args["from_currency"])
		if from == "" {
			from = parseString(args["from"])
		}
		to := parseString(args["to_currency"])
		if to == "" {
			to = parseString(args["to"])
		}
		amt := parseFloat(args["amount"])
		if amt <= 0 {
			amt = 100.0
		}

		res, err := s.forexService.Convert(ctx, &domain.ForexConvertRequest{
			FromCurrency: from,
			ToCurrency:   to,
			Amount:       amt,
		})
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
		}

		text := fmt.Sprintf("Forex Conversion:\n- %.2f %s = %.2f %s\n- Rate: 1 %s = %.4f %s\n- Spread: %.2f%% (~$%.2f USD)",
			res.OriginalAmount, res.FromCurrency, res.ConvertedAmount, res.ToCurrency,
			res.FromCurrency, res.ExchangeRate, res.ToCurrency, res.SpreadFeePct, res.EstimatedFeeUSD)
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "SHOW_FOREX",
			ActionData: map[string]interface{}{
				"from":             res.FromCurrency,
				"to":               res.ToCurrency,
				"original_amount":  res.OriginalAmount,
				"converted_amount": res.ConvertedAmount,
				"exchange_rate":    res.ExchangeRate,
				"spread_fee_pct":   res.SpreadFeePct,
				"estimated_fee_usd": res.EstimatedFeeUSD,
			},
		}

	case "calculate_loan_mortgage":
		p := parseFloat(args["principal"])
		if p <= 0 {
			p = 25000.0
		}
		r := parseFloat(args["annual_rate_pct"])
		if r <= 0 {
			r = 6.5
		}
		t := int(parseFloat(args["term_months"]))
		if t <= 0 {
			t = 60
		}
		loanType := parseString(args["loan_type"])
		if loanType == "" {
			loanType = "PERSONAL"
		}

		calc, err := s.loanService.Calculate(ctx, &domain.LoanCalculateRequest{
			PrincipalAmount: p,
			AnnualRatePct:   r,
			TermMonths:      t,
			LoanType:        loanType,
		})
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
		}

		text := fmt.Sprintf("Loan Simulation (%s):\n- Principal: $%.2f\n- Term: %d months\n- Rate: %.1f%%\n- Monthly Payment: $%.2f/mo\n- Total Interest: $%.2f\n- Total Payment: $%.2f",
			calc.LoanType, calc.PrincipalAmount, calc.TermMonths, calc.AnnualRatePct, calc.MonthlyPayment, calc.TotalInterest, calc.TotalPayment)
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "SHOW_LOAN_CALC",
			ActionData: map[string]interface{}{
				"principal":                calc.PrincipalAmount,
				"annual_rate_pct":          calc.AnnualRatePct,
				"term_months":             calc.TermMonths,
				"loan_type":                calc.LoanType,
				"monthly_payment":          calc.MonthlyPayment,
				"total_payment":            calc.TotalPayment,
				"total_interest":           calc.TotalInterest,
				"estimated_origination_fee": calc.EstimatedOrigination,
			},
		}

	case "manage_beneficiaries":
		action := parseString(args["action"])
		if action == "add" {
			req := domain.AddBeneficiaryRequest{
				Nickname:      parseString(args["nickname"]),
				AccountNumber: parseString(args["account_number"]),
				BankName:      parseString(args["bank_name"]),
			}
			b, err := s.beneficiaryService.AddBeneficiary(ctx, userID, &req)
			if err != nil {
				return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
			}
			return CallToolResult{
				Content:    []ContentItem{{Type: "text", Text: fmt.Sprintf("✅ Saved trusted payee '%s' (%s at %s).", b.Nickname, b.AccountNumber, b.BankName)}},
				ActionType: "SHOW_BENEFICIARIES",
				ActionData: map[string]interface{}{
					"beneficiaries": []map[string]interface{}{
						{"nickname": b.Nickname, "account_number": b.AccountNumber, "bank_name": b.BankName},
					},
				},
			}
		} else {
			list, err := s.beneficiaryService.GetBeneficiaries(ctx, userID)
			if err != nil {
				return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
			}
			return CallToolResult{
				Content:    []ContentItem{{Type: "text", Text: fmt.Sprintf("Retrieved %d saved beneficiaries.", len(list))}},
				ActionType: "SHOW_BENEFICIARIES",
				ActionData: map[string]interface{}{"beneficiaries": list},
			}
		}

	default:
		return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: fmt.Sprintf("Unknown tool '%s'", name)}}}
	}
}
