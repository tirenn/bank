package database

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"bank-core/internal/logger"
	_ "github.com/lib/pq"
	"github.com/pressly/goose/v3"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	gormlogger "gorm.io/gorm/logger"
)

func Connect(dbURL string) (*gorm.DB, *sql.DB, error) {
	ctx := context.Background()

	// 1. Open standard sql.DB connection with retry logic
	sqlDB, err := sql.Open("postgres", dbURL)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to open postgres connection: %w", err)
	}

	sqlDB.SetMaxOpenConns(25)
	sqlDB.SetMaxIdleConns(10)
	sqlDB.SetConnMaxLifetime(5 * time.Minute)

	var pingErr error
	for attempts := 1; attempts <= 10; attempts++ {
		pingErr = sqlDB.PingContext(ctx)
		if pingErr == nil {
			logger.Info(ctx, "Connected to PostgreSQL database successfully", map[string]interface{}{
				"attempts": attempts,
			})
			break
		}
		logger.Warn(ctx, fmt.Sprintf("Waiting for PostgreSQL connection (attempt %d/10)...", attempts), map[string]interface{}{
			"error": pingErr.Error(),
		})
		time.Sleep(1 * time.Second)
	}

	if pingErr != nil {
		return nil, nil, fmt.Errorf("could not connect to postgres after 10 attempts: %w", pingErr)
	}

	// 2. Initialize GORM with standard sqlDB
	gormDB, err := gorm.Open(postgres.New(postgres.Config{
		Conn: sqlDB,
	}), &gorm.Config{
		Logger: gormlogger.Default.LogMode(gormlogger.Warn),
	})
	if err != nil {
		return nil, nil, fmt.Errorf("failed to initialize GORM: %w", err)
	}

	return gormDB, sqlDB, nil
}

func RunMigrations(sqlDB *sql.DB, migrationsDir string) error {
	ctx := context.Background()

	if err := goose.SetDialect("postgres"); err != nil {
		return fmt.Errorf("failed to set goose dialect: %w", err)
	}

	logger.Info(ctx, "Running Goose database migrations...", map[string]interface{}{
		"dir": migrationsDir,
	})

	if err := goose.Up(sqlDB, migrationsDir); err != nil {
		return fmt.Errorf("failed to apply goose migrations: %w", err)
	}

	logger.Info(ctx, "Goose database migrations applied successfully")
	return nil
}
