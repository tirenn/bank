package handler

import (
	"fmt"
	"net/http"

	"bank-core/internal/domain"
	"github.com/gin-gonic/gin"
)


type BeneficiaryHandler struct {
	service domain.BeneficiaryService
}

func NewBeneficiaryHandler(service domain.BeneficiaryService) *BeneficiaryHandler {
	return &BeneficiaryHandler{service: service}
}

func (h *BeneficiaryHandler) List(c *gin.Context) {
	ctx := c.Request.Context()
	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}
	userID := userIDVal.(uint64)

	list, err := h.service.GetBeneficiaries(ctx, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"beneficiaries": list,
		"count":         len(list),
	})
}

func (h *BeneficiaryHandler) Add(c *gin.Context) {
	ctx := c.Request.Context()
	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}
	userID := userIDVal.(uint64)

	var req domain.AddBeneficiaryRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	b, err := h.service.AddBeneficiary(ctx, userID, &req)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message":     "Beneficiary added successfully",
		"beneficiary": b,
	})
}

func (h *BeneficiaryHandler) Delete(c *gin.Context) {
	ctx := c.Request.Context()
	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}
	userID := userIDVal.(uint64)

	idStr := c.Param("id")
	var id uint64
	if _, err := fmt.Sscanf(idStr, "%d", &id); err != nil || id == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid beneficiary ID"})
		return
	}

	if err := h.service.DeleteBeneficiary(ctx, userID, id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Beneficiary removed successfully"})
}

