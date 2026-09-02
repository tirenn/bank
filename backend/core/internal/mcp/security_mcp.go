package mcp

import (
	"context"
	"fmt"
	"net/http"

	"bank-core/internal/domain"
	"github.com/gin-gonic/gin"
)


type SecurityMCPServer struct {
	accountService domain.AccountService
}

func NewSecurityMCPServer(accountService domain.AccountService) *SecurityMCPServer {
	return &SecurityMCPServer{accountService: accountService}
}

func (s *SecurityMCPServer) HandleJSONRPC(c *gin.Context) {
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
				Name:        "lock_unlock_card",
				Description: "Instantly freeze or unfreeze debit card / account for loss or security protection.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"freeze": map[string]interface{}{"type": "boolean", "description": "True to freeze/lock, False to unfreeze/unlock"},
						"reason": map[string]interface{}{"type": "string", "description": "Reason note"},
					},
					"required": []string{"freeze"},
				},
			},
			{
				Name:        "set_spending_limit",
				Description: "Set custom daily transfer and card spending limits for the account.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"daily_limit_dollars": map[string]interface{}{"type": "number", "description": "Daily limit in USD"},
					},
					"required": []string{"daily_limit_dollars"},
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
					Content: []ContentItem{{Type: "text", Text: "Authentication required for security tools."}},
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

func (s *SecurityMCPServer) executeTool(ctx context.Context, userID uint64, name string, args map[string]interface{}) CallToolResult {

	switch name {
	case "lock_unlock_card":
		freeze := false
		if f, ok := args["freeze"].(bool); ok {
			freeze = f
		}
		reason := parseString(args["reason"])
		if reason == "" {
			reason = "Requested via AI Security Assistant"
		}

		acc, err := s.accountService.UpdateStatus(ctx, userID, &domain.UpdateAccountStatusRequest{
			Frozen: freeze,
			Reason: reason,
		})
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
		}

		statusStr := "🔒 FROZEN / LOCKED"
		if !acc.IsFrozen {
			statusStr = "🟢 ACTIVE / UNLOCKED"
		}
		text := fmt.Sprintf("Card & Account Security Control:\n- Status: %s\n- Reason: %s", statusStr, reason)
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "SHOW_LOCK_STATUS",
			ActionData: map[string]interface{}{
				"is_frozen": acc.IsFrozen,
				"status":    acc.Status,
			},
		}

	case "set_spending_limit":
		limitDollars := parseFloat(args["daily_limit_dollars"])
		if limitDollars <= 0 {
			limitDollars = parseFloat(args["limit"])
		}
		if limitDollars <= 0 {
			limitDollars = 5000.0
		}
		limitCents := int64(limitDollars * 100)

		acc, err := s.accountService.UpdateLimits(ctx, userID, &domain.UpdateAccountLimitRequest{
			DailyTransferLimitCents: limitCents,
		})
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
		}

		text := fmt.Sprintf("✅ Daily transfer and card spending limit successfully updated to $%.2f USD.", float64(acc.DailyTransferLimitCents)/100.0)
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "SHOW_LIMITS",
			ActionData: map[string]interface{}{
				"daily_transfer_limit_cents": acc.DailyTransferLimitCents,
				"daily_limit_dollars":        float64(acc.DailyTransferLimitCents) / 100.0,
			},
		}

	default:
		return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: fmt.Sprintf("Unknown tool '%s'", name)}}}
	}
}
