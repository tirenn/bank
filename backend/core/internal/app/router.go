package app

import (
	"time"

	"bank-core/internal/config"
	"bank-core/internal/handler"
	"bank-core/internal/mcp"
	"bank-core/internal/middleware"
	"github.com/gin-contrib/cors"

	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
)

// SetupRouter initializes Gin engine, global middlewares, and API route groups
func SetupRouter(
	cfg *config.Config,
	rdb *redis.Client,
	authHandler *handler.AuthHandler,
	accountHandler *handler.AccountHandler,
	transferHandler *handler.TransferHandler,
	beneficiaryHandler *handler.BeneficiaryHandler,
	forexHandler *handler.ForexHandler,
	loanHandler *handler.LoanHandler,
	aiModelHandler *handler.AIModelHandler,
	txMCPServer *mcp.TransactionMCPServer,
	idMCPServer *mcp.IdentityMCPServer,
	secMCPServer *mcp.SecurityMCPServer,
	wltMCPServer *mcp.WealthMCPServer,
) *gin.Engine {

	gin.SetMode(gin.ReleaseMode)
	router := gin.New()

	// Global Core Middlewares
	router.Use(gin.Recovery())
	router.Use(middleware.RequestIDMiddleware())
	router.Use(middleware.StructuredLoggerMiddleware())

	// CORS Configuration
	corsConfig := cors.DefaultConfig()
	corsConfig.AllowAllOrigins = true
	corsConfig.AllowHeaders = []string{"Origin", "Content-Length", "Content-Type", "Authorization", "Accept", "X-Requested-With", "X-Request-ID", "X-Internal-MCP-Secret"}
	corsConfig.AllowMethods = []string{"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
	router.Use(cors.New(corsConfig))

	// Sliding Window Rate Limiting via Redis
	windowDuration := time.Duration(cfg.RateLimitWin) * time.Second
	router.Use(middleware.RedisSlidingWindowRateLimiter(rdb, cfg.RateLimitReq, windowDuration))

	// Health Check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status":      "healthy",
			"service":     "bank-core-api",
			"orm":         "gorm",
			"rate_limit":  "redis-sliding-window",
			"environment": cfg.Environment,
		})
	})

	// Private MCP Endpoints (Protected by Internal Secret + User JWT)
	mcpGroup := router.Group("/mcp/v1")
	mcpGroup.Use(mcp.PrivateMCPAuthMiddleware(cfg.JWTSecret, cfg.InternalMCPSecret))
	{

		mcpGroup.POST("/transaction", txMCPServer.HandleJSONRPC)
		mcpGroup.POST("/identity", idMCPServer.HandleJSONRPC)
		mcpGroup.POST("/security", secMCPServer.HandleJSONRPC)
		mcpGroup.POST("/wealth", wltMCPServer.HandleJSONRPC)
	}

	// Public Tools & REST APIs
	v1 := router.Group("/api/v1")
	{
		// Public Auth
		auth := v1.Group("/auth")
		{
			auth.POST("/register", authHandler.Register)
			auth.POST("/login", authHandler.Login)
		}

		// Public Calculators & AI Model Discovery
		v1.POST("/forex/convert", forexHandler.Convert)
		v1.POST("/loans/calculate", loanHandler.Calculate)
		v1.GET("/ai/models", aiModelHandler.GetActiveModels)

		// Protected Domain Endpoints
		protected := v1.Group("")
		protected.Use(middleware.AuthMiddleware(cfg.JWTSecret))
		{
			protected.GET("/auth/me", authHandler.Me)
			protected.PUT("/users/address", authHandler.UpdateAddress)
			protected.PUT("/users/kyc", authHandler.UpdateKYC)
			protected.GET("/users/profile", authHandler.Me)

			protected.GET("/accounts", accountHandler.ListMyAccounts)
			protected.POST("/accounts", accountHandler.CreateAccount)
			protected.GET("/accounts/my", accountHandler.GetMyAccount)
			protected.GET("/accounts/lookup/:accountNumber", accountHandler.LookupAccount)
			protected.PUT("/accounts/status", accountHandler.UpdateStatus)
			protected.PUT("/accounts/limits", accountHandler.UpdateLimits)
			protected.POST("/accounts/statements", transferHandler.GenerateStatement)
			protected.GET("/accounts/statements", transferHandler.GenerateStatement)

			protected.POST("/transfers", transferHandler.Transfer)
			protected.POST("/transfers/deposit", transferHandler.Deposit)
			protected.GET("/transactions", transferHandler.GetTransactions)
			protected.GET("/transactions/summary", transferHandler.GetSpendingSummary)
			protected.GET("/transactions/:id", transferHandler.GetTransactionDetail)

			protected.GET("/beneficiaries", beneficiaryHandler.List)
			protected.POST("/beneficiaries", beneficiaryHandler.Add)
			protected.DELETE("/beneficiaries/:id", beneficiaryHandler.Delete)

			// Admin AI Models Management
			protected.GET("/admin/ai/models", aiModelHandler.ListAll)
			protected.POST("/admin/ai/models", aiModelHandler.Create)
			protected.PUT("/admin/ai/models/:id", aiModelHandler.Update)
			protected.DELETE("/admin/ai/models/:id", aiModelHandler.Delete)
		}
	}

	return router
}



