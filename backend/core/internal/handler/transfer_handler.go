package handler

import (
	"net/http"
	"strconv"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
	"github.com/gin-gonic/gin"
)


type TransferHandler struct {
	transferService domain.TransferService
}

func NewTransferHandler(transferService domain.TransferService) *TransferHandler {
	return &TransferHandler{transferService: transferService}
}

func (h *TransferHandler) Transfer(c *gin.Context) {
	ctx := c.Request.Context()

	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	var req domain.TransferRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Warn(ctx, "Invalid transfer request payload", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	userID := userIDVal.(uint64)
	tx, err := h.transferService.Transfer(ctx, userID, &req)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, tx)
}

func (h *TransferHandler) Deposit(c *gin.Context) {
	ctx := c.Request.Context()

	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	var req domain.DepositWithdrawRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Warn(ctx, "Invalid deposit request payload", map[string]interface{}{"error": err.Error()})
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	userID := userIDVal.(uint64)
	tx, err := h.transferService.Deposit(ctx, userID, &req)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, tx)
}

func (h *TransferHandler) GetTransactions(c *gin.Context) {
	ctx := c.Request.Context()

	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	userID := userIDVal.(uint64)

	limitStr := c.DefaultQuery("limit", "50")
	offsetStr := c.DefaultQuery("offset", "0")
	category := c.Query("category")

	limit, _ := strconv.Atoi(limitStr)
	offset, _ := strconv.Atoi(offsetStr)

	txs, err := h.transferService.GetTransactions(ctx, userID, limit, offset, category)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"transactions": txs,
		"count":        len(txs),
		"limit":        limit,
		"offset":       offset,
	})
}

func (h *TransferHandler) GetSpendingSummary(c *gin.Context) {
	ctx := c.Request.Context()

	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	userID := userIDVal.(uint64)
	summary, err := h.transferService.GetSpendingSummary(ctx, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, summary)
}

func (h *TransferHandler) GetTransactionDetail(c *gin.Context) {
	ctx := c.Request.Context()

	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}
	userID := userIDVal.(uint64)
	identifier := c.Param("id")

	tx, err := h.transferService.GetTransactionDetail(ctx, userID, identifier)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, tx)
}

func (h *TransferHandler) GenerateStatement(c *gin.Context) {
	ctx := c.Request.Context()

	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}
	userID := userIDVal.(uint64)

	var req domain.StatementRequest
	_ = c.ShouldBindJSON(&req)

	statement, err := h.transferService.GenerateStatement(ctx, userID, &req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, statement)
}


