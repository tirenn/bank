package handler

import (
	"net/http"

	"bank-core/internal/domain"
	"github.com/gin-gonic/gin"
)


type AIModelHandler struct {
	service domain.AIModelService
}

func NewAIModelHandler(service domain.AIModelService) *AIModelHandler {
	return &AIModelHandler{service: service}
}

// GetActiveModels handles public/client requests to get active AI models ordered by priority
func (h *AIModelHandler) GetActiveModels(c *gin.Context) {
	ctx := c.Request.Context()
	res, err := h.service.GetActiveModels(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, res)
}

// ListAll handles Admin requests to list all AI models with full metadata
func (h *AIModelHandler) ListAll(c *gin.Context) {
	ctx := c.Request.Context()
	models, err := h.service.ListAllModels(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"models": models,
		"count":  len(models),
	})
}

