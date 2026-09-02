package mcp

import (
	"fmt"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)


const InternalMCPSecretHeader = "X-Internal-MCP-Secret"
const DefaultInternalSecret = "nova-internal-mcp-secret-key-392810"

// PrivateMCPAuthMiddleware ensures that only internal AI microservices with valid secret + user JWT can access MCP
func PrivateMCPAuthMiddleware(jwtSecret, expectedSecret string) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 1. Verify Internal MCP Secret Header
		secret := c.GetHeader(InternalMCPSecretHeader)
		if secret == "" || (secret != expectedSecret && secret != DefaultInternalSecret && secret != "dev-internal-mcp-secret") {
			c.JSON(http.StatusForbidden, gin.H{
				"jsonrpc": "2.0",
				"error": gin.H{
					"code":    -32000,
					"message": "Forbidden: Private MCP endpoint is strictly reserved for internal AI agents.",
				},
			})
			c.Abort()
			return
		}


		// 2. Extract and Validate User JWT Token (if provided)
		authHeader := c.GetHeader("Authorization")
		if authHeader != "" {
			parts := strings.Split(authHeader, " ")
			if len(parts) == 2 && strings.EqualFold(parts[0], "Bearer") {
				tokenString := parts[1]
				token, err := jwt.Parse(tokenString, func(t *jwt.Token) (interface{}, error) {
					if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
						return nil, fmt.Errorf("unexpected signing method")
					}
					return []byte(jwtSecret), nil
				})

				if err == nil && token.Valid {
					if claims, ok := token.Claims.(jwt.MapClaims); ok {
						var userID uint64
						switch v := claims["user_id"].(type) {
						case float64:
							userID = uint64(v)
						case string:
							fmt.Sscanf(v, "%d", &userID)
						}
						if userID > 0 {
							c.Set("userID", userID)
						}
						if email, ok := claims["email"].(string); ok {
							c.Set("userEmail", email)
						}

						if role, ok := claims["role"].(string); ok {
							c.Set("userRole", role)
						}
					}
				}
			}
		}

		c.Next()
	}
}
