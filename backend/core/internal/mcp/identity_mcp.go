package mcp

import (
	"context"
	"fmt"
	"net/http"

	"bank-core/internal/domain"
	"github.com/gin-gonic/gin"
)


type IdentityMCPServer struct {
	authService domain.AuthService
}

func NewIdentityMCPServer(authService domain.AuthService) *IdentityMCPServer {
	return &IdentityMCPServer{authService: authService}
}

func (s *IdentityMCPServer) HandleJSONRPC(c *gin.Context) {
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
				Name:        "get_user_profile",
				Description: "Retrieve user's complete legal identity, registered address, and KYC verification status.",
				InputSchema: map[string]interface{}{"type": "object", "properties": map[string]interface{}{}, "required": []string{}},
			},
			{
				Name:        "update_user_address",
				Description: "Update user's legal billing and residential street address.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"street":      map[string]interface{}{"type": "string", "description": "Street name & number"},
						"city":        map[string]interface{}{"type": "string", "description": "City name"},
						"state":       map[string]interface{}{"type": "string", "description": "State code"},
						"postal_code": map[string]interface{}{"type": "string", "description": "Postal ZIP code"},
						"country":     map[string]interface{}{"type": "string", "description": "Country"},
					},
					"required": []string{"street", "city", "state", "postal_code", "country"},
				},
			},
			{
				Name:        "submit_kyc_verification",
				Description: "Submit government identity document (PASSPORT, NATIONAL_ID, DRIVERS_LICENSE) for KYC verification.",
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"doc_type":   map[string]interface{}{"type": "string", "enum": []string{"PASSPORT", "NATIONAL_ID", "DRIVERS_LICENSE"}},
						"doc_number": map[string]interface{}{"type": "string", "description": "Document ID number"},
					},
					"required": []string{"doc_type", "doc_number"},
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
					Content: []ContentItem{{Type: "text", Text: "Authentication required for identity tools."}},
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

func (s *IdentityMCPServer) executeTool(ctx context.Context, userID uint64, name string, args map[string]interface{}) CallToolResult {

	switch name {
	case "get_user_profile":
		user, err := s.authService.GetUserByID(ctx, userID)
		if err != nil || user == nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: "User profile not found."}}}
		}
		addr := fmt.Sprintf("%s, %s, %s %s, %s", user.AddressStreet, user.AddressCity, user.AddressState, user.AddressPostalCode, user.AddressCountry)
		text := fmt.Sprintf("User Profile:\n- Name: %s\n- Email: %s\n- Address: %s\n- KYC: %s (%s)",
			user.FullName, user.Email, addr, user.KYCStatus, user.KYCDocType)
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: text}},
			ActionType: "SHOW_PROFILE",
			ActionData: map[string]interface{}{
				"full_name":           user.FullName,
				"email":               user.Email,
				"address_street":      user.AddressStreet,
				"address_city":        user.AddressCity,
				"address_state":       user.AddressState,
				"address_postal_code": user.AddressPostalCode,
				"address_country":     user.AddressCountry,
				"kyc_status":          user.KYCStatus,
				"kyc_doc_type":        user.KYCDocType,
				"kyc_doc_number":      user.KYCDocNumber,
				"phone_number":        user.PhoneNumber,
			},
		}

	case "update_user_address":
		req := domain.UpdateAddressRequest{
			Street:     parseString(args["street"]),
			City:       parseString(args["city"]),
			State:      parseString(args["state"]),
			PostalCode: parseString(args["postal_code"]),
			Country:    parseString(args["country"]),
		}
		updated, err := s.authService.UpdateAddress(ctx, userID, &req)
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
		}
		addr := fmt.Sprintf("%s, %s, %s %s, %s", updated.AddressStreet, updated.AddressCity, updated.AddressState, updated.AddressPostalCode, updated.AddressCountry)
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: fmt.Sprintf("✅ Residential address updated successfully to: %s", addr)}},
			ActionType: "SHOW_PROFILE",
			ActionData: map[string]interface{}{
				"full_name":           updated.FullName,
				"email":               updated.Email,
				"address_street":      updated.AddressStreet,
				"address_city":        updated.AddressCity,
				"address_state":       updated.AddressState,
				"address_postal_code": updated.AddressPostalCode,
				"address_country":     updated.AddressCountry,
				"kyc_status":          updated.KYCStatus,
				"kyc_doc_type":        updated.KYCDocType,
				"kyc_doc_number":      updated.KYCDocNumber,
			},
		}

	case "submit_kyc_verification":
		req := domain.UpdateKYCRequest{
			DocType:   parseString(args["doc_type"]),
			DocNumber: parseString(args["doc_number"]),
		}
		updated, err := s.authService.UpdateKYC(ctx, userID, &req)
		if err != nil {
			return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: err.Error()}}}
		}
		return CallToolResult{
			Content:    []ContentItem{{Type: "text", Text: fmt.Sprintf("✅ KYC verification approved for %s (#%s). Status: VERIFIED.", updated.KYCDocType, updated.KYCDocNumber)}},
			ActionType: "SHOW_PROFILE",
			ActionData: map[string]interface{}{
				"full_name":      updated.FullName,
				"email":          updated.Email,
				"kyc_status":     updated.KYCStatus,
				"kyc_doc_type":   updated.KYCDocType,
				"kyc_doc_number": updated.KYCDocNumber,
			},
		}

	default:
		return CallToolResult{IsError: true, Content: []ContentItem{{Type: "text", Text: fmt.Sprintf("Unknown tool '%s'", name)}}}
	}
}
