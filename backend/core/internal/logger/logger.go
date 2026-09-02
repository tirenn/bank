package logger

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"runtime"
	"time"
)

type LogLevel string

const (
	LevelDebug LogLevel = "DEBUG"
	LevelInfo  LogLevel = "INFO"
	LevelWarn  LogLevel = "WARN"
	LevelError LogLevel = "ERROR"
)

type LogEntry struct {
	Timestamp   string                 `json:"timestamp"`
	Level       LogLevel               `json:"level"`
	Service     string                 `json:"service"`
	Environment string                 `json:"environment"`
	RequestID   string                 `json:"request_id,omitempty"`
	TraceID     string                 `json:"trace_id,omitempty"`
	Caller      string                 `json:"caller,omitempty"`
	Message     string                 `json:"message"`
	Error       string                 `json:"error,omitempty"`
	Fields      map[string]interface{} `json:"fields,omitempty"`
}

type ctxKey string

const RequestIDKey ctxKey = "request_id"
const TraceIDKey ctxKey = "trace_id"

var (
	ServiceName = "bank-core"
	Environment = "development"
)

func Init(service string, env string) {
	if service != "" {
		ServiceName = service
	}
	if env != "" {
		Environment = env
	}
}

func logMessage(ctx context.Context, level LogLevel, msg string, err error, fields map[string]interface{}) {
	reqID := ""
	traceID := ""
	if ctx != nil {
		if val, ok := ctx.Value(RequestIDKey).(string); ok {
			reqID = val
		}
		if val, ok := ctx.Value(TraceIDKey).(string); ok {
			traceID = val
		}
	}

	caller := ""
	if _, file, line, ok := runtime.Caller(2); ok {
		caller = fmt.Sprintf("%s:%d", file, line)
	}

	entry := LogEntry{
		Timestamp:   time.Now().UTC().Format(time.RFC3339Nano),
		Level:       level,
		Service:     ServiceName,
		Environment: Environment,
		RequestID:   reqID,
		TraceID:     traceID,
		Caller:      caller,
		Message:     msg,
		Fields:      fields,
	}

	if err != nil {
		entry.Error = err.Error()
	}

	jsonBytes, _ := json.Marshal(entry)
	fmt.Fprintln(os.Stdout, string(jsonBytes))
}

func Info(ctx context.Context, msg string, fields ...map[string]interface{}) {
	var f map[string]interface{}
	if len(fields) > 0 {
		f = fields[0]
	}
	logMessage(ctx, LevelInfo, msg, nil, f)
}

func Warn(ctx context.Context, msg string, fields ...map[string]interface{}) {
	var f map[string]interface{}
	if len(fields) > 0 {
		f = fields[0]
	}
	logMessage(ctx, LevelWarn, msg, nil, f)
}

func Error(ctx context.Context, msg string, err error, fields ...map[string]interface{}) {
	var f map[string]interface{}
	if len(fields) > 0 {
		f = fields[0]
	}
	logMessage(ctx, LevelError, msg, err, f)
}

func Debug(ctx context.Context, msg string, fields ...map[string]interface{}) {
	var f map[string]interface{}
	if len(fields) > 0 {
		f = fields[0]
	}
	logMessage(ctx, LevelDebug, msg, nil, f)
}
