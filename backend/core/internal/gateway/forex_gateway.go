package gateway

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"
	"sync"
	"time"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
	"github.com/redis/go-redis/v9"
)

type openErApiResponse struct {
	Result   string             `json:"result"`
	BaseCode string             `json:"base_code"`
	Rates    map[string]float64 `json:"rates"`
}

// Fallback baseline rates relative to USD (1.00 USD) in case external network is temporarily unreachable
var defaultFallbackRates = map[string]float64{
	"USD": 1.00,
	"EUR": 0.92,
	"GBP": 0.79,
	"JPY": 154.20,
	"SGD": 1.34,
	"IDR": 16250.00,
	"CAD": 1.36,
	"AUD": 1.52,
	"CHF": 0.88,
	"CNY": 7.24,
	"HKD": 7.82,
	"NZD": 1.68,
}

// ForexGateway handles communication with external forex rate providers, Redis caching, and in-memory caches.
type ForexGateway struct {
	apiURL     string
	rdb        *redis.Client
	httpClient *http.Client
	mu         sync.RWMutex
	memCache   map[string]float64
	lastFetch  time.Time
}

func NewForexGateway(apiURL string, rdb *redis.Client) domain.ForexRateProvider {
	if apiURL == "" {
		apiURL = "https://open.er-api.com/v6/latest/USD"
	}
	return &ForexGateway{
		apiURL: apiURL,
		rdb:    rdb,
		httpClient: &http.Client{
			Timeout: 6 * time.Second,
		},
		memCache: make(map[string]float64),
	}
}

func (g *ForexGateway) GetRates(ctx context.Context) (map[string]float64, error) {
	// 1. Check in-memory cache (valid for 15 minutes)
	g.mu.RLock()
	if time.Since(g.lastFetch) < 15*time.Minute && len(g.memCache) > 0 {
		cachedCopy := make(map[string]float64, len(g.memCache))
		for k, v := range g.memCache {
			cachedCopy[k] = v
		}
		g.mu.RUnlock()
		return cachedCopy, nil
	}
	g.mu.RUnlock()

	// 2. Check Redis cache (1 hour TTL)
	if g.rdb != nil {
		cachedJSON, err := g.rdb.Get(ctx, "forex:rates:usd").Result()
		if err == nil && cachedJSON != "" {
			var rates map[string]float64
			if err := json.Unmarshal([]byte(cachedJSON), &rates); err == nil && len(rates) > 0 {
				g.mu.Lock()
				g.memCache = rates
				g.lastFetch = time.Now()
				g.mu.Unlock()
				return rates, nil
			}
		}
	}

	// 3. Fetch live rates from Free Real-Time Forex API endpoint
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, g.apiURL, nil)
	if err == nil {
		resp, doErr := g.httpClient.Do(req)
		if doErr == nil && resp.StatusCode == http.StatusOK {
			defer resp.Body.Close()
			var apiData openErApiResponse
			if jsonErr := json.NewDecoder(resp.Body).Decode(&apiData); jsonErr == nil && strings.ToLower(apiData.Result) == "success" && len(apiData.Rates) > 0 {
				// Store in memory cache
				g.mu.Lock()
				g.memCache = apiData.Rates
				g.lastFetch = time.Now()
				g.mu.Unlock()

				// Store in Redis with 1-hour expiration
				if g.rdb != nil {
					if encoded, encErr := json.Marshal(apiData.Rates); encErr == nil {
						_ = g.rdb.Set(ctx, "forex:rates:usd", string(encoded), 1*time.Hour).Err()
					}
				}

				logger.Info(ctx, "Successfully fetched live real-time forex exchange rates from gateway", map[string]interface{}{
					"api_url":     g.apiURL,
					"total_rates": len(apiData.Rates),
				})
				return apiData.Rates, nil
			}
		} else if doErr != nil {
			logger.Warn(ctx, "Failed to connect to live forex API gateway, falling back to cached baseline", map[string]interface{}{
				"error":   doErr.Error(),
				"api_url": g.apiURL,
			})
		}
	}

	// 4. Return fallback baseline rates if API is unavailable
	return defaultFallbackRates, nil
}
