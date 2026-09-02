package middleware

import (
	"fmt"
	"net/http"
	"strings"
	"time"

	"bank-core/internal/logger"
	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)


// AuthMiddleware verifies JWT authorization tokens
func AuthMiddleware(jwtSecret string) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx := c.Request.Context()

		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header is required"})
			c.Abort()
			return
		}

		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid Authorization header format. Expected Bearer <token>"})
			c.Abort()
			return
		}

		tokenString := parts[1]
		token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
			}
			return []byte(jwtSecret), nil
		})

		if err != nil || !token.Valid {
			logger.Warn(ctx, "Invalid or expired JWT token attempted", map[string]interface{}{
				"error": err.Error(),
			})
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid or expired token"})
			c.Abort()
			return
		}

		claims, ok := token.Claims.(jwt.MapClaims)
		if !ok {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token claims payload"})
			c.Abort()
			return
		}

		var userID uint64
		switch v := claims["user_id"].(type) {
		case float64:
			userID = uint64(v)
		case string:
			fmt.Sscanf(v, "%d", &userID)
		}

		if userID == 0 {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid user_id in token"})
			c.Abort()
			return
		}


		userRole, _ := claims["role"].(string)
		if userRole == "" {
			userRole = "CUSTOMER"
		}

		c.Set("userID", userID)
		c.Set("userEmail", claims["email"])
		c.Set("userRole", userRole)
		c.Next()
	}
}

// RequireRole enforces Role-Based Access Control (RBAC)
func RequireRole(allowedRoles ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		roleVal, exists := c.Get("userRole")
		if !exists {
			c.JSON(http.StatusForbidden, gin.H{"error": "Access denied: missing role context"})
			c.Abort()
			return
		}

		userRole, ok := roleVal.(string)
		if !ok {
			c.JSON(http.StatusForbidden, gin.H{"error": "Access denied: invalid role format"})
			c.Abort()
			return
		}

		for _, allowed := range allowedRoles {
			if strings.EqualFold(userRole, allowed) {
				c.Next()
				return
			}
		}

		c.JSON(http.StatusForbidden, gin.H{
			"error": fmt.Sprintf("Access denied: role '%s' is not authorized for this resource", userRole),
		})
		c.Abort()
	}
}

// StructuredLoggerMiddleware logs each incoming HTTP request in Grafana Loki JSON format
func StructuredLoggerMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		startTime := time.Now()
		path := c.Request.URL.Path
		rawQuery := c.Request.URL.RawQuery

		c.Next()

		latency := time.Since(startTime)
		statusCode := c.Writer.Status()
		ctx := c.Request.Context()

		fields := map[string]interface{}{
			"status":     statusCode,
			"method":     c.Request.Method,
			"path":       path,
			"query":      rawQuery,
			"ip":         c.ClientIP(),
			"user_agent": c.Request.UserAgent(),
			"latency_ms": float64(latency.Microseconds()) / 1000.0,
		}

		if len(c.Errors) > 0 {
			for _, e := range c.Errors {
				logger.Error(ctx, "HTTP request error", e.Err, fields)
			}
		} else if statusCode >= 500 {
			logger.Error(ctx, "HTTP 5xx Server Error", fmt.Errorf("server error with status %d", statusCode), fields)
		} else if statusCode >= 400 {
			logger.Warn(ctx, "HTTP 4xx Client Error", fields)
		} else {
			logger.Info(ctx, "HTTP Request", fields)
		}
	}
}
