package main

import (
	"log"

	"bank-core/internal/app"
)

func main() {
	if err := app.Run(); err != nil {
		log.Fatalf("Bank Core application error: %v", err)
	}
}
