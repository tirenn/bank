package app

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"bank-core/internal/config"
	"bank-core/internal/database"
	"bank-core/internal/handler"
	"bank-core/internal/logger"
	"bank-core/internal/mcp"
	"bank-core/internal/repository"

	"bank-core/internal/service"
	"github.com/redis/go-redis/v9"
)

// Run initializes configuration, dependencies, database connections, routers, and manages the HTTP server lifecycle.
func Run() error {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	// 1. Load Configuration via Viper
	cfg, err := config.Load()
	if err != nil {
		return fmt.Errorf("failed to load configuration: %w", err)
	}

	logger.Init("bank-core", cfg.Environment)
	logger.Info(ctx, "Initializing Bank Core Application", map[string]interface{}{
		"port":        cfg.Port,
		"environment": cfg.Environment,
	})

	// 2. Connect Database & Run Goose Migrations
	gormDB, sqlDB, err := database.Connect(cfg.DatabaseURL)
	if err != nil {
		return fmt.Errorf("database connection error: %w", err)
	}
	defer sqlDB.Close()

	if err := database.RunMigrations(sqlDB, "migrations"); err != nil {
		return fmt.Errorf("migration runner error: %w", err)
	}

	// 3. Seed Demo Data
	if err := database.SeedDatabase(gormDB); err != nil {
		logger.Warn(ctx, "Database seeder note", map[string]interface{}{"error": err.Error()})
	}

	// 4. Connect Redis for Sliding Window Rate Limiting
	rdb := redis.NewClient(&redis.Options{
		Addr: cfg.RedisURL,
	})
	if pingErr := rdb.Ping(ctx).Err(); pingErr != nil {
		logger.Warn(ctx, "Redis offline, rate limiter will fail open", map[string]interface{}{
			"redis_url": cfg.RedisURL,
			"error":     pingErr.Error(),
		})
	} else {
		logger.Info(ctx, "Redis connected for sliding window rate limiter", map[string]interface{}{
			"redis_url": cfg.RedisURL,
		})
	}
	defer rdb.Close()

	// 5. Dependency Injection Wiring (Clean Architecture by Domain)
	userRepo := repository.NewUserRepository(gormDB)
	accountRepo := repository.NewAccountRepository(gormDB)
	txRepo := repository.NewTransactionRepository(gormDB)
	beneficiaryRepo := repository.NewBeneficiaryRepository(gormDB)

	authService := service.NewAuthService(userRepo, accountRepo, cfg.JWTSecret)
	accountService := service.NewAccountService(accountRepo, userRepo)
	transferService := service.NewTransferService(txRepo, accountRepo)
	beneficiaryService := service.NewBeneficiaryService(beneficiaryRepo)
	forexService := service.NewForexService()
	loanService := service.NewLoanService()

	authHandler := handler.NewAuthHandler(authService)
	accountHandler := handler.NewAccountHandler(accountService)
	transferHandler := handler.NewTransferHandler(transferService)
	beneficiaryHandler := handler.NewBeneficiaryHandler(beneficiaryService)
	forexHandler := handler.NewForexHandler(forexService)
	loanHandler := handler.NewLoanHandler(loanService)

	// 5.1 Private MCP Domain Servers
	txMCPServer := mcp.NewTransactionMCPServer(accountService, transferService)
	idMCPServer := mcp.NewIdentityMCPServer(authService)
	secMCPServer := mcp.NewSecurityMCPServer(accountService)
	wltMCPServer := mcp.NewWealthMCPServer(forexService, loanService, beneficiaryService)

	// 6. Setup HTTP Router
	router := SetupRouter(
		cfg,
		rdb,
		authHandler,
		accountHandler,
		transferHandler,
		beneficiaryHandler,
		forexHandler,
		loanHandler,
		txMCPServer,
		idMCPServer,
		secMCPServer,
		wltMCPServer,
	)



	// 7. Start HTTP Server
	srv := &http.Server{
		Addr:    ":" + cfg.Port,
		Handler: router,
	}

	go func() {
		logger.Info(ctx, "HTTP Server listening", map[string]interface{}{"port": cfg.Port})
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error(ctx, "HTTP server failed to serve", err)
			os.Exit(1)
		}
	}()

	// 8. Graceful Shutdown
	<-ctx.Done()
	logger.Info(context.Background(), "Server received shutdown signal. Terminating gracefully...")

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		return fmt.Errorf("graceful shutdown failed: %w", err)
	}

	logger.Info(context.Background(), "Bank Core Application stopped successfully")
	return nil
}
