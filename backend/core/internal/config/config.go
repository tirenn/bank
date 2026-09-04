package config

import (
	"fmt"
	"strings"

	"github.com/spf13/viper"
)

type Config struct {
	Port              string `mapstructure:"PORT"`
	DatabaseURL       string `mapstructure:"DATABASE_URL"`
	JWTSecret         string `mapstructure:"JWT_SECRET"`
	InternalMCPSecret string `mapstructure:"INTERNAL_MCP_SECRET"`
	RedisURL          string `mapstructure:"REDIS_URL"`
	RateLimitReq      int    `mapstructure:"RATE_LIMIT_REQUESTS"`
	RateLimitWin      int    `mapstructure:"RATE_LIMIT_WINDOW_SEC"`
	Environment       string `mapstructure:"ENVIRONMENT"`
	ForexAPIURL       string `mapstructure:"FOREX_API_URL"`
	DefaultTransferOTP string `mapstructure:"DEFAULT_TRANSFER_OTP"`
}

func Load() (*Config, error) {
	v := viper.New()

	v.SetDefault("PORT", "8082")
	v.SetDefault("DATABASE_URL", "postgres://postgres_user111:password123!!!@localhost:5432/bank_db?sslmode=disable")
	v.SetDefault("JWT_SECRET", "super-secret-bank-jwt-key-change-in-prod-123456")
	v.SetDefault("INTERNAL_MCP_SECRET", "nova-internal-mcp-secret-key-392810")
	v.SetDefault("REDIS_URL", "localhost:6379")
	v.SetDefault("RATE_LIMIT_REQUESTS", 60)
	v.SetDefault("RATE_LIMIT_WINDOW_SEC", 60)
	v.SetDefault("ENVIRONMENT", "development")
	v.SetDefault("FOREX_API_URL", "https://open.er-api.com/v6/latest/USD")
	v.SetDefault("DEFAULT_TRANSFER_OTP", "888888")



	v.SetConfigFile(".env")
	v.SetConfigType("env")
	v.AutomaticEnv()
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))

	if err := v.ReadInConfig(); err != nil {
		// It's acceptable if .env is missing and values come from system environment
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			// Ignore not found error if environment variables exist
		}
	}

	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("unable to decode configuration into struct: %w", err)
	}

	return &cfg, nil
}
