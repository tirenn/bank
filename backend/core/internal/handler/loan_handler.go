package handler

import (
	"net/http"

	"bank-core/internal/domain"
	"github.com/gin-gonic/gin"
)

type LoanHandler struct {
	loanService domain.LoanService
}

func NewLoanHandler(loanService domain.LoanService) *LoanHandler {
	return &LoanHandler{loanService: loanService}
}

func (h *LoanHandler) Calculate(c *gin.Context) {
	var req domain.LoanCalculateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	res, err := h.loanService.Calculate(c.Request.Context(), &req)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, res)
}
