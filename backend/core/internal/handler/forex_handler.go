package handler

import (
	"net/http"

	"bank-core/internal/domain"
	"github.com/gin-gonic/gin"
)

type ForexHandler struct {
	forexService domain.ForexService
}

func NewForexHandler(forexService domain.ForexService) *ForexHandler {
	return &ForexHandler{forexService: forexService}
}

func (h *ForexHandler) Convert(c *gin.Context) {
	var req domain.ForexConvertRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	res, err := h.forexService.Convert(c.Request.Context(), &req)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, res)
}
