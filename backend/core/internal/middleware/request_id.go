package middleware

import (
	"context"

	"bank-core/internal/logger"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

const HeaderXRequestID = "X-Request-ID"

// RequestIDMiddleware extracts or generates a unique X-Request-ID per request
func RequestIDMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		reqID := c.GetHeader(HeaderXRequestID)
		if reqID == "" {
			reqID = uuid.New().String()
		}

		c.Header(HeaderXRequestID, reqID)
		c.Set(string(logger.RequestIDKey), reqID)

		// Inject request_id into standard Go context
		ctx := context.WithValue(c.Request.Context(), logger.RequestIDKey, reqID)
		c.Request = c.Request.WithContext(ctx)

		c.Next()
	}
}
