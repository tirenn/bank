package mcp

import (
	"context"
	"fmt"
	"net/http"
	"strconv"
	"strings"

	"bank-core/internal/domain"
	"github.com/gin-gonic/gin"
)


type TransactionMCPServer struct {
	accountService domain.AccountService
	transferService domain.TransferService
}

func NewTransactionMCPServer(accountService domain.AccountService, transferService domain.TransferService) *TransactionMCPServer {
	return &TransactionMCPServer{
		accountService: accountService,
		transferService: transferService,
	}
}

func (s *TransactionMCPServer) HandleJSONRPC(c *gin.Context) {
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
				Name:        "get_balance",
				Description: "Retrieve current bank balance for a specific account number or card number. If identifier is omitted and user has multiple accounts, returns the accounts list prompting the user to specify by account number or card number.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"account_number": map[string]interface{}{
							"type":        "string",
							"description": "Optional: Bank Account Number (e.g. ACC-10029384) or Account Name (e.g. Primary Checking)",
						},
						"card_number": map[string]interface{}{
							"type":        "string",
							"description": "Optional: Full 16-digit Card Number or last 4 digits (e.g. '5412 7721 9012 4431' or '4431')",
						},
						"account_identifier": map[string]interface{}{
							"type":        "string",
							"description": "Optional: Account Number, Card Number (or last 4 digits), or Account Name",
						},
					},
				},
			},

			{
				Name:        "get_transactions",
				Description: "Retrieve recent ledger transaction history with optional category and limit filters.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"limit":    map[string]interface{}{"type": "integer", "description": "Number of transactions to return (1-50)"},
						"category": map[string]interface{}{"type": "string", "description": "Filter by category"},
					},
				},
			},
			{
				Name:        "draft_transfer",
				Description: "Validate recipient and prepare fund transfer confirmation draft.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"to_account_number": map[string]interface{}{"type": "string", "description": "Recipient account number"},
						"amount":            map[string]interface{}{"type": "number", "description": "Amount in dollars"},
						"description":       map[string]interface{}{"type": "string", "description": "Transfer note"},
						"category":          map[string]interface{}{"type": "string", "description": "Transfer category"},
					},
					"required": []string{"to_account_number", "amount"},
				},
			},
			{
				Name:        "get_transaction_details",
				Description: "Retrieve complete audit receipt for a transaction reference number or ID.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"identifier": map[string]interface{}{"type": "string", "description": "Reference number (e.g. TRF-...) or UUID"},
					},
					"required": []string{"identifier"},
				},
			},
			{
				Name:        "get_all_accounts",
				Description: "Retrieve all bank accounts, cards, and balances owned by the user.",
				InputSchema: map[string]interface{}{"type": "object", "properties": map[string]interface{}{}, "required": []string{}},
			},
			{
				Name:        "open_new_account",
				Description: "Instantly create/open a new bank account with virtual/physical credit or debit card.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"account_name":            map[string]interface{}{"type": "string", "description": "Account nickname e.g. Vacation Savings, Tech Investment"},
						"account_type":            map[string]interface{}{"type": "string", "enum": []string{"SAVINGS", "CHECKING", "INVESTMENT"}},
						"currency":                map[string]interface{}{"type": "string", "description": "Currency code e.g. USD, EUR, IDR"},
						"card_brand":              map[string]interface{}{"type": "string", "enum": []string{"VISA", "MASTERCARD"}},
						"initial_deposit_dollars": map[string]interface{}{"type": "number", "description": "Initial deposit amount in dollars"},
					},
					"required": []string{"account_name"},
				},
			},
			{
				Name:        "request_account_statement",
				Description: "Generate official periodic account statement with starting/ending balance and inflows/outflows.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"start_date": map[string]interface{}{"type": "string", "description": "Start date YYYY-MM-DD"},
						"end_date":   map[string]interface{}{"type": "string", "description": "End date YYYY-MM-DD"},
					},
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

		if !hasUser {
			c.JSON(http.StatusOK, JSONRPCResponse{
				JSONRPC: "2.0",
				ID:      req.ID,
				Result: CallToolResult{
					IsError: true,
					Content: []ContentItem{{Type: "text", Text: "Authentication required for transaction tools."}},
				},
			})
			return
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

func (s *TransactionMCPServer) executeTool(ctx context.Context, userID uint64, name string, args map[string]interface{}) CallToolResult {

	switch name {
	case "get_balance":
		res, err := s.accountService.ListUserAccounts(ctx, userID)
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
		}
		if len(res.Accounts) == 0 {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: "No bank accounts found for this user."}}}
		}

		targetAccNum := strings.TrimSpace(parseString(args["account_number"]))
		targetCardNum := strings.TrimSpace(parseString(args["card_number"]))
		targetIdent := strings.TrimSpace(parseString(args["account_identifier"]))

		if targetIdent != "" {
			if strings.HasPrefix(strings.ToUpper(targetIdent), "ACC-") && targetAccNum == "" {
				targetAccNum = targetIdent
			} else if targetCardNum == "" {
				targetCardNum = targetIdent
			}
		}

		cleanTargetCard := strings.ReplaceAll(strings.ReplaceAll(targetCardNum, " ", ""), "-", "")

		var matched *domain.Account
		hasTargetFilter := targetAccNum != "" || targetCardNum != "" || targetIdent != ""

		if hasTargetFilter {
			for i := range res.Accounts {
				acc := &res.Accounts[i]
				cleanAccCard := strings.ReplaceAll(strings.ReplaceAll(acc.CardNumber, " ", ""), "-", "")

				if targetAccNum != "" && strings.EqualFold(acc.AccountNumber, targetAccNum) {
					matched = acc
					break
				}
				if cleanTargetCard != "" && (cleanAccCard == cleanTargetCard || strings.HasSuffix(cleanAccCard, cleanTargetCard)) {
					matched = acc
					break
				}
				if targetIdent != "" && (strings.EqualFold(acc.AccountNumber, targetIdent) || strings.EqualFold(acc.AccountName, targetIdent) || strings.EqualFold(acc.CardBrand, targetIdent)) {
					matched = acc
					break
				}
			}

			if matched == nil {
				return CallToolResult{
					IsError: true,
					Content: []ContentItem{{Type: "text", Text: fmt.Sprintf("Access Denied: Account or card '%s' does not belong to your profile or does not exist. You are only authorized to view balances for your own accounts.", targetIdent)}},
				}
			}

		} else {
			if len(res.Accounts) == 1 {
				matched = &res.Accounts[0]
			} else {
				var sb strings.Builder
				sb.WriteString(fmt.Sprintf("You have %d bank accounts. Which account would you like to check? Please specify the **Account Number** or **Card Number**:\n\n", len(res.Accounts)))
				for i, acc := range res.Accounts {
					cardMasked := acc.CardNumber
					if len(cardMasked) >= 4 {
						cardMasked = "..." + cardMasked[len(cardMasked)-4:]
					}
					bal := float64(acc.BalanceCents) / 100.0
					sb.WriteString(fmt.Sprintf("%d. **%s** — Account: `%s` | Card: `%s %s` | Balance: $%.2f\n",
						i+1, acc.AccountName, acc.AccountNumber, acc.CardBrand, cardMasked, bal))
				}
				sb.WriteString("\nPlease tell me which **Account Number** (e.g. `ACC-10029384`) or **Card Number** (or last 4 digits) to check.")
				return CallToolResult{
					Content:    []ContentItem{{Type: "text", Text: sb.String()}},
					ActionType: "SHOW_ACCOUNTS",
					ActionData: map[string]interface{}{
						"accounts": res.Accounts,
						"count":    res.Count,
					},
				}
			}
		}

		bal := float64(matched.BalanceCents) / 100.0
		text := fmt.Sprintf("Account Details:\n- Owner: %s\n- Account Name: %s\n- Account Number: %s\n- Card: %s (%s)\n- Available Balance: $%.2f %s\n- Status: %s",
			res.User.FullName, matched.AccountName, matched.AccountNumber, matched.CardBrand, matched.CardNumber, bal, matched.Currency, matched.Status)
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "SHOW_BALANCE",
			ActionData: map[string]interface{}{
				"account_id":      matched.ID,
				"account_name":    matched.AccountName,
				"account_number":  matched.AccountNumber,
				"card_number":     matched.CardNumber,
				"card_brand":      matched.CardBrand,
				"balance_dollars": bal,
				"currency":        matched.Currency,
				"owner_name":      res.User.FullName,
				"status":          matched.Status,
			},
		}



	case "get_transactions":
		limit := 5
		if l, ok := args["limit"].(float64); ok {
			limit = int(l)
		}
		cat, _ := args["category"].(string)
		txs, err := s.transferService.GetTransactions(ctx, userID, limit, 0, cat)
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
		}
		text := fmt.Sprintf("Retrieved %d recent transaction records.", len(txs))
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "SHOW_TRANSACTIONS",
			ActionData: map[string]interface{}{"transactions": txs},
		}

	case "draft_transfer":
		toAcc, _ := args["to_account_number"].(string)
		amt, _ := args["amount"].(float64)
		desc, _ := args["description"].(string)
		cat, _ := args["category"].(string)
		if desc == "" {
			desc = "Transfer via AI Assistant"
		}
		if cat == "" {
			cat = "Transfer"
		}

		info, err := s.accountService.LookupAccount(ctx, toAcc)
		recipientName := "Verified Account"
		if err == nil {
			if nameStr, ok := info["owner_name"].(string); ok {
				recipientName = nameStr
			}
		}

		draft := map[string]interface{}{
			"to_account_number": toAcc,
			"recipient_name":    recipientName,
			"amount_dollars":    amt,
			"amount_cents":      int64(amt * 100),
			"description":       desc,
			"category":          cat,
		}
		text := fmt.Sprintf("Transfer Authorization Draft:\n- Recipient: %s (%s)\n- Amount: $%.2f\n- Note: %s\nPlease confirm via card in chat.",
			recipientName, toAcc, amt, desc)
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "CONFIRM_TRANSFER",
			ActionData: draft,
		}

	case "get_transaction_details":
		idStr, _ := args["identifier"].(string)
		tx, err := s.transferService.GetTransactionDetail(ctx, userID, idStr)
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: "Transaction not found."}}}
		}
		amt := float64(tx.AmountCents) / 100.0
		text := fmt.Sprintf("Transaction Receipt (%s):\n- Ref: %s\n- Amount: $%.2f\n- Description: %s\n- Counterparty: %s",
			tx.Type, tx.ReferenceNumber, amt, tx.Description, tx.CounterpartyName)
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "SHOW_TRANSACTION_DETAIL",
			ActionData: map[string]interface{}{
				"reference_number": tx.ReferenceNumber,
				"amount_cents":     tx.AmountCents,
				"type":             tx.Type,
				"description":      tx.Description,
				"category":         tx.Category,
				"counterparty_name": tx.CounterpartyName,
				"counterparty_account_num": tx.CounterpartyAccountNum,
				"created_at":       tx.CreatedAt.String(),
			},
		}

	case "get_all_accounts":
		res, err := s.accountService.ListUserAccounts(ctx, userID)
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
		}
		text := fmt.Sprintf("You have %d active bank accounts.", res.Count)
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "SHOW_ACCOUNTS",
			ActionData: map[string]interface{}{
				"accounts": res.Accounts,
				"count":    res.Count,
			},
		}

	case "open_new_account":
		accName := parseString(args["account_name"])
		if accName == "" {
			accName = "Savings Account"
		}
		accType := parseString(args["account_type"])
		if accType == "" {
			accType = "SAVINGS"
		}
		curr := parseString(args["currency"])
		if curr == "" {
			curr = "USD"
		}
		brand := parseString(args["card_brand"])
		if brand == "" {
			brand = "VISA"
		}
		deposit := parseFloat(args["initial_deposit_dollars"])

		acc, err := s.accountService.CreateAccount(ctx, userID, &domain.CreateAccountRequest{
			AccountName:           accName,
			AccountType:           accType,
			Currency:              curr,
			CardBrand:             brand,
			InitialDepositDollars: deposit,
		})
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
		}

		balDollars := float64(acc.BalanceCents) / 100.0
		text := fmt.Sprintf("🎉 New Bank Account & Card Issued Successfully!\n- Account Name: %s (%s)\n- Account Number: %s\n- %s Card Number: %s\n- Card Expiry: %s | CVV: %s\n- Initial Balance: $%.2f %s",
			acc.AccountName, acc.AccountType, acc.AccountNumber, acc.CardBrand, acc.CardNumber, acc.CardExpiry, acc.CardCVV, balDollars, acc.Currency)

		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "SHOW_NEW_ACCOUNT",
			ActionData: map[string]interface{}{
				"account_id":       acc.ID,
				"account_number":   acc.AccountNumber,
				"account_name":     acc.AccountName,
				"account_type":     acc.AccountType,
				"card_number":      acc.CardNumber,
				"card_brand":       acc.CardBrand,
				"card_expiry":      acc.CardExpiry,
				"card_cvv":         acc.CardCVV,
				"balance_dollars":  balDollars,
				"currency":         acc.Currency,
				"status":           acc.Status,
			},
		}

	case "request_account_statement":

		req := domain.StatementRequest{}
		stm, err := s.transferService.GenerateStatement(ctx, userID, &req)
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
		}
		text := fmt.Sprintf("Account Statement (%s):\n- Starting Balance: $%.2f\n- Ending Balance: $%.2f\n- Total Inflow: +$%.2f\n- Total Outflow: -$%.2f",
			stm.StatementID, float64(stm.StartingBalanceCents)/100.0, float64(stm.EndingBalanceCents)/100.0,
			float64(stm.TotalDepositsCents)/100.0, float64(stm.TotalWithdrawalsCents)/100.0)
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "SHOW_STATEMENT",
			ActionData: map[string]interface{}{
				"statement_id":           stm.StatementID,
				"account_number":         stm.AccountNumber,
				"starting_balance_cents": stm.StartingBalanceCents,
				"ending_balance_cents":   stm.EndingBalanceCents,
				"total_deposits_cents":   stm.TotalDepositsCents,
				"total_withdrawals_cents": stm.TotalWithdrawalsCents,
				"transaction_count":      stm.TransactionCount,
				"period_start":           stm.PeriodStart.String(),
				"period_end":             stm.PeriodEnd.String(),
			},
		}

	default:
		return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: fmt.Sprintf("Unknown tool '%s'", name)}}}
	}
}

func parseString(v interface{}) string {
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}

func parseFloat(v interface{}) float64 {
	switch n := v.(type) {
	case float64:
		return n
	case int:
		return float64(n)
	case string:
		f, _ := strconv.ParseFloat(n, 64)
		return f
	}
	return 0
}

func parseUint(v interface{}) uint64 {
	switch n := v.(type) {
	case float64:
		return uint64(n)
	case int:
		return uint64(n)
	case int64:
		return uint64(n)
	case uint64:
		return n
	case string:
		u, _ := strconv.ParseUint(strings.TrimSpace(n), 10, 64)
		return u
	}
	return 0
}

