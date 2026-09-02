package middleware

import (
	"context"

	"bank-core/internal/logger"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

const HeaderXRequestID = "X-Request-ID"
const HeaderXTraceID = "X-Trace-ID"

// RequestIDMiddleware extracts or generates a unique X-Request-ID and X-Trace-ID per request
func RequestIDMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		reqID := c.GetHeader(HeaderXRequestID)
		if reqID == "" {
			reqID = uuid.New().String()
		}

		traceID := c.GetHeader(HeaderXTraceID)
		if traceID == "" {
			traceID = reqID
		}

		c.Header(HeaderXRequestID, reqID)
		c.Header(HeaderXTraceID, traceID)
		c.Set(string(logger.RequestIDKey), reqID)
		c.Set(string(logger.TraceIDKey), traceID)

		// Inject request_id and trace_id into standard Go context
		ctx := context.WithValue(c.Request.Context(), logger.RequestIDKey, reqID)
		ctx = context.WithValue(ctx, logger.TraceIDKey, traceID)
		c.Request = c.Request.WithContext(ctx)

		c.Next()
	}
}

