package handler

import (
	"fmt"
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

// Create handles Admin requests to add a new AI model to the database
func (h *AIModelHandler) Create(c *gin.Context) {
	ctx := c.Request.Context()
	var req domain.CreateAIModelRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	model, err := h.service.CreateModel(ctx, &req)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "AI Model created successfully in database",
		"model":   model,
	})
}

// Update handles Admin requests to modify an existing AI model
func (h *AIModelHandler) Update(c *gin.Context) {
	ctx := c.Request.Context()
	idStr := c.Param("id")
	var id uint64
	if _, err := fmt.Sscanf(idStr, "%d", &id); err != nil || id == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid model ID"})
		return
	}

	var req domain.UpdateAIModelRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	model, err := h.service.UpdateModel(ctx, id, &req)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "AI Model updated successfully in database",
		"model":   model,
	})
}

// Delete handles Admin requests to remove an AI model from the database
func (h *AIModelHandler) Delete(c *gin.Context) {
	ctx := c.Request.Context()
	idStr := c.Param("id")
	var id uint64
	if _, err := fmt.Sscanf(idStr, "%d", &id); err != nil || id == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid model ID"})
		return
	}

	if err := h.service.DeleteModel(ctx, id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "AI Model deleted successfully from database"})
}
