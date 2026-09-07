package mcp_test

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"bank-core/internal/domain"
	"bank-core/internal/mcp"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type MockAccountService struct {
	mock.Mock
}

func (m *MockAccountService) GetUserAccount(ctx context.Context, userID uint64) (*domain.AccountDetailResponse, error) {
	args := m.Called(ctx, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.AccountDetailResponse), args.Error(1)
}

func (m *MockAccountService) ListUserAccounts(ctx context.Context, userID uint64) (*domain.UserAccountsResponse, error) {
	args := m.Called(ctx, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.UserAccountsResponse), args.Error(1)
}

func (m *MockAccountService) CreateAccount(ctx context.Context, userID uint64, req *domain.CreateAccountRequest) (*domain.Account, error) {
	args := m.Called(ctx, userID, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Account), args.Error(1)
}

func (m *MockAccountService) LookupAccount(ctx context.Context, accountNumber string) (map[string]interface{}, error) {
	args := m.Called(ctx, accountNumber)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(map[string]interface{}), args.Error(1)
}

func (m *MockAccountService) UpdateStatus(ctx context.Context, userID uint64, req *domain.UpdateAccountStatusRequest) (*domain.Account, error) {
	args := m.Called(ctx, userID, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Account), args.Error(1)
}

func (m *MockAccountService) UpdateLimits(ctx context.Context, userID uint64, req *domain.UpdateAccountLimitRequest) (*domain.Account, error) {
	args := m.Called(ctx, userID, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Account), args.Error(1)
}

func (m *MockAccountService) ResolveAccountByIdentifier(ctx context.Context, userID uint64, identifier string) (*domain.Account, error) {
	args := m.Called(ctx, userID, identifier)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Account), args.Error(1)
}

type MockTransferService struct {
	mock.Mock
}

func (m *MockTransferService) DraftTransfer(ctx context.Context, userID uint64, req *domain.DraftTransferRequest) (*domain.TransferDraftResponse, error) {
	args := m.Called(ctx, userID, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.TransferDraftResponse), args.Error(1)
}

func (m *MockTransferService) Transfer(ctx context.Context, userID uint64, req *domain.TransferRequest) (*domain.Transaction, error) {
	args := m.Called(ctx, userID, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func (m *MockTransferService) Deposit(ctx context.Context, userID uint64, req *domain.DepositWithdrawRequest) (*domain.Transaction, error) {
	args := m.Called(ctx, userID, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func (m *MockTransferService) GetTransactions(ctx context.Context, userID uint64, limit int, offset int, category string) ([]domain.Transaction, error) {
	args := m.Called(ctx, userID, limit, offset, category)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]domain.Transaction), args.Error(1)
}

func (m *MockTransferService) GetTransactionDetail(ctx context.Context, userID uint64, identifier string) (*domain.Transaction, error) {
	args := m.Called(ctx, userID, identifier)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func (m *MockTransferService) GetSpendingSummary(ctx context.Context, userID uint64) (*domain.SpendingSummary, error) {
	args := m.Called(ctx, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.SpendingSummary), args.Error(1)
}

func (m *MockTransferService) GenerateStatement(ctx context.Context, userID uint64, req *domain.StatementRequest) (*domain.StatementResponse, error) {
	args := m.Called(ctx, userID, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.StatementResponse), args.Error(1)
}

func setupTestServer(accSvc domain.AccountService, txSvc domain.TransferService, userID uint64) *gin.Engine {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	server := mcp.NewTransactionMCPServer(accSvc, txSvc)

	r.POST("/mcp/transactions", func(c *gin.Context) {
		if userID > 0 {
			c.Set("userID", userID)
		}
		server.HandleJSONRPC(c)
	})
	return r
}

func sendMCPCall(r *gin.Engine, toolName string, args map[string]interface{}) (mcp.JSONRPCResponse, mcp.CallToolResult) {
	reqBody := mcp.JSONRPCRequest{
		JSONRPC: "2.0",
		ID:      1,
		Method:  "tools/call",
		Params: map[string]interface{}{
			"name":      toolName,
			"arguments": args,
		},
	}
	raw, _ := json.Marshal(reqBody)

	req, _ := http.NewRequest("POST", "/mcp/transactions", bytes.NewBuffer(raw))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	var rpcResp mcp.JSONRPCResponse
	_ = json.Unmarshal(w.Body.Bytes(), &rpcResp)

	var toolResult mcp.CallToolResult
	if rpcResp.Result != nil {
		resBytes, _ := json.Marshal(rpcResp.Result)
		_ = json.Unmarshal(resBytes, &toolResult)
	}
	return rpcResp, toolResult
}

func TestDraftTransfer_MCP_ErrorDelegation(t *testing.T) {
	mockAcc := new(MockAccountService)
	mockTx := new(MockTransferService)
	router := setupTestServer(mockAcc, mockTx, 1001)

	mockTx.On("DraftTransfer", mock.Anything, uint64(1001), mock.MatchedBy(func(req *domain.DraftTransferRequest) bool {
		return req.ToAccountNumber == "ACC-99998888" && req.AmountDollars == 50.0
	})).Return(nil, errors.New("insufficient funds in account ACC-10001111"))

	_, res := sendMCPCall(router, "draft_transfer", map[string]interface{}{
		"to_account_number": "ACC-99998888",
		"amount":            50.0,
	})

	assert.True(t, res.IsError)
	assert.Contains(t, res.Content[0].Text, "insufficient funds")
	assert.Empty(t, res.ActionType)
	mockTx.AssertExpectations(t)
}

func TestDraftTransfer_MCP_SuccessDelegation(t *testing.T) {
	mockAcc := new(MockAccountService)
	mockTx := new(MockTransferService)
	router := setupTestServer(mockAcc, mockTx, 1001)

	expectedDraft := &domain.TransferDraftResponse{
		FromAccountID:     10,
		FromAccountNumber: "ACC-10001111",
		ToAccountNumber:   "ACC-99998888",
		RecipientName:     "Bob Receiver",
		AmountDollars:     75.50,
		AmountCents:       7550,
		Description:       "Dinner split",
		Category:          "Transfer",
		SummaryText:       "Transfer Authorization Draft: $75.50 to Bob Receiver",
	}

	mockTx.On("DraftTransfer", mock.Anything, uint64(1001), mock.MatchedBy(func(req *domain.DraftTransferRequest) bool {
		return req.ToAccountNumber == "ACC-99998888" && req.AmountDollars == 75.50
	})).Return(expectedDraft, nil)

	_, res := sendMCPCall(router, "draft_transfer", map[string]interface{}{
		"to_account_number": "ACC-99998888",
		"amount":            75.50,
		"description":       "Dinner split",
	})

	assert.False(t, res.IsError)
	assert.Equal(t, "CONFIRM_TRANSFER", res.ActionType)
	assert.NotNil(t, res.ActionData)
	assert.Equal(t, "ACC-99998888", res.ActionData["to_account_number"])
	assert.Equal(t, "ACC-10001111", res.ActionData["from_account_number"])
	assert.Equal(t, "Bob Receiver", res.ActionData["recipient_name"])
	assert.Equal(t, 75.50, res.ActionData["amount_dollars"])
	assert.Equal(t, "Transfer Authorization Draft: $75.50 to Bob Receiver", res.Content[0].Text)
	mockTx.AssertExpectations(t)
}

func TestGetBalance_MCP_ResolveIdentifierDelegation(t *testing.T) {
	mockAcc := new(MockAccountService)
	mockTx := new(MockTransferService)
	router := setupTestServer(mockAcc, mockTx, 1001)

	mockAcc.On("ListUserAccounts", mock.Anything, uint64(1001)).Return(&domain.UserAccountsResponse{
		Accounts: []domain.Account{
			{ID: 1, AccountNumber: "ACC-1001", AccountName: "Primary Checking", BalanceCents: 50000, Status: "ACTIVE"},
			{ID: 2, AccountNumber: "ACC-1002", AccountName: "Secondary Savings", BalanceCents: 150000, Status: "ACTIVE"},
		},
		Count: 2,
		User:  domain.User{FullName: "Alice Wonder"},
	}, nil)

	mockAcc.On("ResolveAccountByIdentifier", mock.Anything, uint64(1001), "ACC-1002").Return(&domain.Account{
		ID:            2,
		AccountNumber: "ACC-1002",
		AccountName:   "Secondary Savings",
		BalanceCents:  150000,
		Status:        "ACTIVE",
		Currency:      "USD",
		CardBrand:     "VISA",
		CardNumber:    "4532 9999 8888 7777",
	}, nil)

	_, res := sendMCPCall(router, "get_balance", map[string]interface{}{
		"account_number": "ACC-1002",
	})

	assert.False(t, res.IsError)
	assert.Equal(t, "SHOW_BALANCE", res.ActionType)
	assert.Equal(t, 1500.0, res.ActionData["balance_dollars"])
	assert.Equal(t, "ACC-1002", res.ActionData["account_number"])
	mockAcc.AssertExpectations(t)
}
