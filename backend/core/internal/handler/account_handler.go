package handler

import (
	"net/http"

	"bank-core/internal/domain"
	"github.com/gin-gonic/gin"
)


type AccountHandler struct {
	accountService domain.AccountService
}

func NewAccountHandler(accountService domain.AccountService) *AccountHandler {
	return &AccountHandler{accountService: accountService}
}

func (h *AccountHandler) GetMyAccount(c *gin.Context) {
	ctx := c.Request.Context()

	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	userID := userIDVal.(uint64)
	detail, err := h.accountService.GetUserAccount(ctx, userID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, detail)
}

func (h *AccountHandler) ListMyAccounts(c *gin.Context) {
	ctx := c.Request.Context()

	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	userID := userIDVal.(uint64)
	res, err := h.accountService.ListUserAccounts(ctx, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, res)
}

func (h *AccountHandler) CreateAccount(c *gin.Context) {
	ctx := c.Request.Context()

	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	userID := userIDVal.(uint64)
	var req domain.CreateAccountRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	acc, err := h.accountService.CreateAccount(ctx, userID, &req)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "New bank account & card generated successfully",
		"account": acc,
	})
}


func (h *AccountHandler) LookupAccount(c *gin.Context) {
	ctx := c.Request.Context()

	accountNumber := c.Param("accountNumber")
	if accountNumber == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Account number parameter is required"})
		return
	}

	info, err := h.accountService.LookupAccount(ctx, accountNumber)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, info)
}

func (h *AccountHandler) UpdateStatus(c *gin.Context) {
	ctx := c.Request.Context()

	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}
	userID := userIDVal.(uint64)

	var req domain.UpdateAccountStatusRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	acc, err := h.accountService.UpdateStatus(ctx, userID, &req)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":   "Account card lock status updated successfully",
		"account":   acc,
		"is_frozen": acc.IsFrozen,
		"status":    acc.Status,
	})
}

func (h *AccountHandler) UpdateLimits(c *gin.Context) {
	ctx := c.Request.Context()

	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}
	userID := userIDVal.(uint64)

	var req domain.UpdateAccountLimitRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if req.DailyTransferLimitCents <= 0 {
		req.DailyTransferLimitCents = 500000 // default to $5,000.00
	}

	acc, err := h.accountService.UpdateLimits(ctx, userID, &req)

	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":                    "Account spending and transfer limits updated",
		"daily_transfer_limit_cents": acc.DailyTransferLimitCents,
		"daily_limit_dollars":        float64(acc.DailyTransferLimitCents) / 100.0,
	})
}


