# Multi-Stage Dockerfile for Bank Core Service
FROM golang:1.26-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o /app/server ./cmd/api/main.go

# Production Image
FROM alpine:3.19

WORKDIR /app

RUN apk --no-cache add ca-certificates tzdata curl

COPY --from=builder /app/server /app/server
COPY --from=builder /app/migrations /app/migrations
COPY --from=builder /app/.env.example /app/.env.example

EXPOSE 8082

CMD ["/app/server"]
