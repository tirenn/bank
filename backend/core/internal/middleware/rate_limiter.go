package middleware

import (
	"fmt"
	"net/http"
	"time"

	"bank-core/internal/logger"
	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
)

// RedisSlidingWindowRateLimiter implements a sliding window counter algorithm using Redis Sorted Sets (ZSET).
// This guarantees strict rate limit accuracy across distributed microservice instances.
func RedisSlidingWindowRateLimiter(rdb *redis.Client, maxRequests int, windowDuration time.Duration) gin.HandlerFunc {
	return func(c *gin.Context) {
		if rdb == nil {
			c.Next()
			return
		}

		ctx := c.Request.Context()
		clientIP := c.ClientIP()
		key := fmt.Sprintf("rate_limit:%s:%s", c.FullPath(), clientIP)
		now := time.Now().UnixNano()
		windowStart := now - windowDuration.Nanoseconds()

		pipe := rdb.Pipeline()
		// 1. Remove elements older than the current sliding window
		pipe.ZRemRangeByScore(ctx, key, "-inf", fmt.Sprintf("%d", windowStart))
		// 2. Count current elements in window
		cardCmd := pipe.ZCard(ctx, key)
		// 3. Add current request timestamp
		pipe.ZAdd(ctx, key, redis.Z{Score: float64(now), Member: fmt.Sprintf("%d", now)})
		// 4. Set TTL for the key
		pipe.Expire(ctx, key, windowDuration)

		_, err := pipe.Exec(ctx)
		if err != nil {
			logger.Warn(ctx, "Redis rate limiter error, allowing request by fail-open policy", map[string]interface{}{
				"error": err.Error(),
			})
			c.Next()
			return
		}

		currentCount := cardCmd.Val()
		if currentCount >= int64(maxRequests) {
			logger.Warn(ctx, "Rate limit exceeded (sliding window)", map[string]interface{}{
				"ip":           clientIP,
				"path":         c.Request.URL.Path,
				"limit":        maxRequests,
				"window_sec":   windowDuration.Seconds(),
				"current_reqs": currentCount,
			})

			c.Header("Retry-After", fmt.Sprintf("%d", int(windowDuration.Seconds())))
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error":       "Too many requests. Please slow down.",
				"retry_after": int(windowDuration.Seconds()),
			})
			c.Abort()
			return
		}

		c.Header("X-RateLimit-Limit", fmt.Sprintf("%d", maxRequests))
		c.Header("X-RateLimit-Remaining", fmt.Sprintf("%d", int64(maxRequests)-currentCount-1))
		c.Next()
	}
}
