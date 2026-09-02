package database

import (
	"context"
	"fmt"
	"time"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

func SeedDatabase(db *gorm.DB) error {
	ctx := context.Background()

	var count int64
	if err := db.WithContext(ctx).Model(&domain.User{}).Count(&count).Error; err != nil {
		return fmt.Errorf("failed to count existing users: %w", err)
	}

	hashedPassword, err := bcrypt.GenerateFromPassword([]byte("password123"), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash demo password: %w", err)
	}

	// Always ensure Admin User exists and has an Account
	var adminUser domain.User
	if err := db.WithContext(ctx).Where("email = ?", "admin@bank.com").First(&adminUser).Error; err != nil {
		adminUser = domain.User{
			Email:        "admin@bank.com",
			PasswordHash: string(hashedPassword),
			FullName:     "System Administrator",
			Role:         "ADMIN",
			CreatedAt:    time.Now().AddDate(0, -2, 0),
		}
		if err := db.WithContext(ctx).Create(&adminUser).Error; err != nil {
			logger.Error(ctx, "Failed to create seed admin user", err)
		} else {
			logger.Info(ctx, "Created default seed admin user: admin@bank.com")
		}
	}

	var adminAcc domain.Account
	if err := db.WithContext(ctx).Where("user_id = ?", adminUser.ID).First(&adminAcc).Error; err != nil {
		adminAcc = domain.Account{
			UserID:        adminUser.ID,
			AccountNumber: "ACC-00000001",
			BalanceCents:  100000000, // $1,000,000.00 Master Treasury
			Currency:      "USD",
			Status:        "ACTIVE",
			CreatedAt:     time.Now().AddDate(0, -2, 0),
		}
		if err := db.WithContext(ctx).Create(&adminAcc).Error; err != nil {
			logger.Error(ctx, "Failed to create seed admin treasury account", err)
		} else {
			logger.Info(ctx, "Created default seed admin treasury account: ACC-00000001")
		}
	}

	// Always ensure AI Models are seeded if table is empty
	if err := SeedAIModels(db); err != nil {
		logger.Warn(ctx, "AI model seeder note", map[string]interface{}{"error": err.Error()})
	}

	if count > 0 {
		logger.Info(ctx, "Database already seeded. Skipping other seeders.", map[string]interface{}{"user_count": count})
		return nil
	}



	logger.Info(ctx, "Seeding database with demo users, accounts, and transactions via GORM...")

	// 2. User 1: John Doe
	user1 := domain.User{
		Email:             "john.doe@bank.com",
		PasswordHash:      string(hashedPassword),
		FullName:          "John Doe",
		Role:              "CUSTOMER",
		AddressStreet:     "450 Wall St",
		AddressCity:       "New York",
		AddressState:      "NY",
		AddressPostalCode: "10005",
		AddressCountry:    "United States",
		PhoneNumber:       "+1 (555) 019-2834",
		KYCStatus:         "VERIFIED",
		KYCDocType:        "PASSPORT",
		KYCDocNumber:      "US-PASS-992019",
		CreatedAt:         time.Now().AddDate(0, -1, 0),
	}

	// 3. User 2: Sarah Smith
	user2 := domain.User{
		Email:             "sarah.smith@bank.com",
		PasswordHash:      string(hashedPassword),
		FullName:          "Sarah Smith",
		Role:              "CUSTOMER",
		AddressStreet:     "120 Market St",
		AddressCity:       "San Francisco",
		AddressState:      "CA",
		AddressPostalCode: "94105",
		AddressCountry:    "United States",
		PhoneNumber:       "+1 (555) 982-1144",
		KYCStatus:         "VERIFIED",
		KYCDocType:        "DRIVERS_LICENSE",
		KYCDocNumber:      "CA-DL-883920",
		CreatedAt:         time.Now().AddDate(0, -1, 0),
	}

	// 4. User 3: Alice Johnson
	user3 := domain.User{
		Email:             "alice.johnson@bank.com",
		PasswordHash:      string(hashedPassword),
		FullName:          "Alice Johnson",
		Role:              "CUSTOMER",
		AddressStreet:     "742 Evergreen Terrace",
		AddressCity:       "Springfield",
		AddressState:      "OR",
		AddressPostalCode: "97477",
		AddressCountry:    "United States",
		PhoneNumber:       "+1 (555) 321-7788",
		KYCStatus:         "VERIFIED",
		KYCDocType:        "NATIONAL_ID",
		KYCDocNumber:      "US-ID-449102",
		CreatedAt:         time.Now().AddDate(0, -1, 0),
	}

	users := []domain.User{user1, user2, user3}
	for i := range users {
		if err := db.WithContext(ctx).Create(&users[i]).Error; err != nil {
			return fmt.Errorf("failed to insert seed user: %w", err)
		}
	}

	// Accounts (John Doe has 2 accounts: Checking & High-Yield Savings)
	acc1 := domain.Account{
		UserID:                  users[0].ID,
		AccountNumber:           "ACC-10029384",
		AccountName:             "Primary Checking",
		AccountType:             "CHECKING",
		CardNumber:              "4532 8920 1823 9042",
		CardBrand:               "VISA",
		CardExpiry:              "08/29",
		CardCVV:                 "832",
		BalanceCents:            1254050, // $12,540.50
		Currency:                "USD",
		Status:                  "ACTIVE",
		DailyTransferLimitCents: 1000000,
		IsFrozen:                false,
		CreatedAt:               time.Now().AddDate(0, -1, 0),
	}

	acc2 := domain.Account{
		UserID:                  users[0].ID,
		AccountNumber:           "ACC-29481029",
		AccountName:             "High-Yield Growth Savings",
		AccountType:             "SAVINGS",
		CardNumber:              "5412 7721 9012 4431",
		CardBrand:               "MASTERCARD",
		CardExpiry:              "11/30",
		CardCVV:                 "419",
		BalanceCents:            3500000, // $35,000.00
		Currency:                "USD",
		Status:                  "ACTIVE",
		DailyTransferLimitCents: 2000000,
		IsFrozen:                false,
		CreatedAt:               time.Now().AddDate(0, -1, 0),
	}

	acc3 := domain.Account{
		UserID:                  users[1].ID,
		AccountNumber:           "ACC-83920194",
		AccountName:             "Primary Checking",
		AccountType:             "CHECKING",
		CardNumber:              "4532 1102 9940 3381",
		CardBrand:               "VISA",
		CardExpiry:              "04/28",
		CardCVV:                 "291",
		BalanceCents:            482000, // $4,820.00
		Currency:                "USD",
		Status:                  "ACTIVE",
		DailyTransferLimitCents: 500000,
		IsFrozen:                false,
		CreatedAt:               time.Now().AddDate(0, -1, 0),
	}

	acc4 := domain.Account{
		UserID:                  users[2].ID,
		AccountNumber:           "ACC-54910283",
		AccountName:             "Primary Checking",
		AccountType:             "CHECKING",
		CardNumber:              "5412 6632 8812 5590",
		CardBrand:               "MASTERCARD",
		CardExpiry:              "01/29",
		CardCVV:                 "604",
		BalanceCents:            890000, // $8,900.00
		Currency:                "USD",
		Status:                  "ACTIVE",
		DailyTransferLimitCents: 500000,
		IsFrozen:                false,
		CreatedAt:               time.Now().AddDate(0, -1, 0),
	}

	accounts := []domain.Account{acc1, acc2, acc3, acc4}
	for i := range accounts {
		if err := db.WithContext(ctx).Create(&accounts[i]).Error; err != nil {
			return fmt.Errorf("failed to insert seed account: %w", err)
		}
	}


	// Saved Beneficiaries for John Doe
	ben1 := domain.Beneficiary{
		UserID:        users[0].ID,
		Nickname:      "Sarah Smith (Rent)",
		AccountNumber: "ACC-83920194",
		BankName:      "AURA Core Bank",
		CreatedAt:     time.Now().AddDate(0, -1, 0),
	}
	ben2 := domain.Beneficiary{
		UserID:        users[0].ID,
		Nickname:      "Alice Johnson (Consulting)",
		AccountNumber: "ACC-54910283",
		BankName:      "AURA Core Bank",
		CreatedAt:     time.Now().AddDate(0, -1, 0),
	}
	_ = db.WithContext(ctx).Create(&[]domain.Beneficiary{ben1, ben2}).Error

	// Sample Transactions for John Doe
	txs := []struct {
		Type        domain.TransactionType
		Amount      int64
		Description string
		Category    string
		CounterNum  string
		CounterName string
		Ref         string
		DaysAgo     int
	}{
		{domain.TransactionDeposit, 500000, "Monthly Salary Deposit - Acme Tech Corp", "Salary", "", "", "REF-SALARY-01", 28},
		{domain.TransactionTransferOut, 120000, "Monthly Apartment Rent Payment", "Housing", "ACC-83920194", "Sarah Smith", "REF-RENT-01", 25},
		{domain.TransactionTransferOut, 8550, "Dinner with colleagues at Bistro Grill", "Dining", "", "Bistro Grill", "REF-DINING-01", 20},
		{domain.TransactionTransferOut, 14500, "Weekly Grocery Run at SuperMarket", "Groceries", "", "WholeFoods", "REF-GROC-01", 18},
		{domain.TransactionTransferOut, 1599, "Netflix Premium Streaming Plan", "Subscriptions", "", "Netflix Inc", "REF-SUB-01", 15},
		{domain.TransactionTransferOut, 24000, "Electric & High-Speed Internet Bill", "Utilities", "", "City Power & Light", "REF-UTIL-01", 10},
		{domain.TransactionTransferIn, 35000, "Project Consulting Bonus", "Income", "ACC-54910283", "Alice Johnson", "REF-INC-02", 7},
		{domain.TransactionTransferOut, 4500, "Uber rides downtown", "Transportation", "", "Uber BV", "REF-UBER-01", 5},
		{domain.TransactionTransferOut, 12000, "Shopping at Tech Gadgets Store", "Shopping", "", "BestElectronics", "REF-SHOP-01", 2},
		{domain.TransactionTransferOut, 2500, "Coffee & snacks with team", "Dining", "", "Starbucks", "REF-COFFEE-01", 1},
	}

	var txEntities []domain.Transaction
	for _, item := range txs {
		txEntities = append(txEntities, domain.Transaction{
			AccountID:              accounts[0].ID,
			Type:                   item.Type,
			AmountCents:            item.Amount,
			Description:            item.Description,
			Category:               item.Category,
			CounterpartyAccountNum: item.CounterNum,
			CounterpartyName:       item.CounterName,
			ReferenceNumber:        item.Ref,
			CreatedAt:              time.Now().AddDate(0, 0, -item.DaysAgo),
		})
	}

	if err := db.WithContext(ctx).Create(&txEntities).Error; err != nil {
		return fmt.Errorf("failed to insert seed transactions: %w", err)
	}

	logger.Info(ctx, "Seeder completed successfully with GORM")
	return nil
}

func SeedAIModels(db *gorm.DB) error {
	ctx := context.Background()

	var modelCount int64
	if err := db.WithContext(ctx).Model(&domain.AIModel{}).Count(&modelCount).Error; err != nil {
		logger.Warn(ctx, "Failed to count AI models", map[string]interface{}{"error": err.Error()})
		return err
	}

	if modelCount > 0 {
		logger.Info(ctx, "AI models already present in database. Skipping AI model seeding.", map[string]interface{}{
			"count": modelCount,
		})
		return nil
	}

	logger.Info(ctx, "Seeding AI models in PostgreSQL database...")

	modelSeeds := []struct {
		Slug string
		Name string
	}{
		{"nvidia/nemotron-3-ultra-550b-a55b:free", "NVIDIA Nemotron 3 Ultra 550B"},
		{"nvidia/nemotron-3-super-120b-a12b:free", "NVIDIA Nemotron 3 Super 120B"},
		{"meta-llama/llama-3.3-70b-instruct:free", "Meta Llama 3.3 70B Instruct"},
		{"nousresearch/hermes-3-llama-3.1-405b:free", "Hermes 3 Llama 3.1 405B"},
		{"google/gemma-4-31b-it:free", "Google Gemma 4 31B"},
		{"google/gemma-4-26b-a4b-it:free", "Google Gemma 4 26B"},
		{"qwen/qwen3-next-80b-a3b-instruct:free", "Qwen 3 Next 80B Instruct"},
		{"openai/gpt-oss-20b:free", "OpenAI GPT OSS 20B"},
		{"z-ai/glm-5.2:free", "Z-AI GLM 5.2"},
		{"minimax/minimax-m3-20260531:free", "MiniMax M3"},
		{"cognitivecomputations/dolphin-mistral-24b-venice-edition:free", "Dolphin Mistral 24B Venice"},
		{"tencent/hy3:free", "Tencent HY3"},
		{"openrouter/free", "OpenRouter Free Auto-Router"},
	}

	for i, item := range modelSeeds {
		aiModel := domain.AIModel{
			Name:      item.Name,
			ModelID:   item.Slug,
			Provider:  "openrouter",
			IsFree:    true,
			IsActive:  true,
			Priority:  i + 1,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
		if err := db.WithContext(ctx).Where("model_id = ?", item.Slug).FirstOrCreate(&aiModel).Error; err != nil {
			logger.Error(ctx, fmt.Sprintf("Failed to seed model %s", item.Slug), err)
		}
	}

	logger.Info(ctx, fmt.Sprintf("Seeded %d AI models into PostgreSQL successfully", len(modelSeeds)))
	return nil
}


