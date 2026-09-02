package service

import (
	"context"
	"crypto/rand"
	"errors"
	"fmt"
	"math/big"
	"time"

	"bank-core/internal/domain"
	"bank-core/internal/logger"
	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)


type AuthService struct {
	userRepo    domain.UserRepository
	accountRepo domain.AccountRepository
	jwtSecret   string
}

func NewAuthService(userRepo domain.UserRepository, accountRepo domain.AccountRepository, jwtSecret string) domain.AuthService {
	return &AuthService{
		userRepo:    userRepo,
		accountRepo: accountRepo,
		jwtSecret:   jwtSecret,
	}
}

func (s *AuthService) Register(ctx context.Context, req *domain.RegisterRequest) (*domain.AuthResponse, error) {
	existingUser, err := s.userRepo.FindByEmail(ctx, req.Email)
	if err != nil {
		logger.Error(ctx, "Error checking user existence during registration", err, map[string]interface{}{"email": req.Email})
		return nil, err
	}
	if existingUser != nil {
		return nil, errors.New("email is already registered")
	}

	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		logger.Error(ctx, "Failed to hash password", err)
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}

	user := domain.User{
		Email:        req.Email,
		PasswordHash: string(hashedPassword),
		FullName:     req.FullName,
		CreatedAt:    time.Now(),
	}

	if err := s.userRepo.Create(ctx, &user); err != nil {
		return nil, err
	}

	// Create default checking account with initial bonus credit
	randomNum, _ := rand.Int(rand.Reader, big.NewInt(89999999))
	accNum := fmt.Sprintf("ACC-%08d", randomNum.Int64()+10000000)

	account := domain.Account{
		UserID:        user.ID,
		AccountNumber: accNum,
		BalanceCents:  100000, // $1,000.00 welcome initial credit
		Currency:      "USD",
		Status:        "ACTIVE",
		CreatedAt:     time.Now(),
	}

	if err := s.accountRepo.Create(ctx, &account); err != nil {
		return nil, err
	}

	role := user.Role
	if role == "" {
		role = "CUSTOMER"
	}
	user.Role = role

	token, err := s.generateJWT(user.ID, user.Email, user.Role)
	if err != nil {
		logger.Error(ctx, "Failed to generate JWT", err)
		return nil, err
	}

	logger.Info(ctx, "New user registered successfully", map[string]interface{}{
		"user_id": user.ID,
		"email":   user.Email,
		"role":    user.Role,
	})

	return &domain.AuthResponse{
		Token: token,
		User:  user,
	}, nil
}

func (s *AuthService) Login(ctx context.Context, req *domain.LoginRequest) (*domain.AuthResponse, error) {
	user, err := s.userRepo.FindByEmail(ctx, req.Email)
	if err != nil {
		logger.Error(ctx, "Login database error", err, map[string]interface{}{"email": req.Email})
		return nil, err
	}
	if user == nil {
		logger.Warn(ctx, "Login failed: user not found", map[string]interface{}{"email": req.Email})
		return nil, errors.New("invalid email or password")
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
		logger.Warn(ctx, "Login failed: incorrect password", map[string]interface{}{"email": req.Email})
		return nil, errors.New("invalid email or password")
	}

	if user.Role == "" {
		user.Role = "CUSTOMER"
	}

	token, err := s.generateJWT(user.ID, user.Email, user.Role)
	if err != nil {
		logger.Error(ctx, "Failed to issue JWT token", err)
		return nil, err
	}

	logger.Info(ctx, "User authenticated successfully", map[string]interface{}{
		"user_id": user.ID,
		"email":   user.Email,
		"role":    user.Role,
	})

	return &domain.AuthResponse{
		Token: token,
		User:  *user,
	}, nil
}

func (s *AuthService) GetUserByID(ctx context.Context, id uint64) (*domain.User, error) {
	return s.userRepo.FindByID(ctx, id)
}

func (s *AuthService) UpdateAddress(ctx context.Context, userID uint64, req *domain.UpdateAddressRequest) (*domain.User, error) {
	user, err := s.userRepo.FindByID(ctx, userID)
	if err != nil {
		return nil, err
	}
	if user == nil {
		return nil, errors.New("user not found")
	}

	user.AddressStreet = req.Street
	user.AddressCity = req.City
	user.AddressState = req.State
	user.AddressPostalCode = req.PostalCode
	user.AddressCountry = req.Country

	if err := s.userRepo.Update(ctx, user); err != nil {
		return nil, err
	}

	logger.Info(ctx, "User address updated successfully", map[string]interface{}{
		"user_id": userID,
		"city":    req.City,
		"country": req.Country,
	})

	return user, nil
}

func (s *AuthService) UpdateKYC(ctx context.Context, userID uint64, req *domain.UpdateKYCRequest) (*domain.User, error) {
	user, err := s.userRepo.FindByID(ctx, userID)
	if err != nil {
		return nil, err
	}
	if user == nil {
		return nil, errors.New("user not found")
	}

	now := time.Now()
	user.KYCDocType = req.DocType
	user.KYCDocNumber = req.DocNumber
	user.KYCStatus = "VERIFIED"
	user.KYCVerifiedAt = &now

	if err := s.userRepo.Update(ctx, user); err != nil {
		return nil, err
	}

	logger.Info(ctx, "User KYC status updated to VERIFIED", map[string]interface{}{
		"user_id":    userID,
		"doc_type":   req.DocType,
		"doc_number": req.DocNumber,
	})

	return user, nil
}

func (s *AuthService) generateJWT(userID uint64, email string, role string) (string, error) {
	claims := jwt.MapClaims{
		"user_id": userID,
		"email":   email,
		"role":    role,
		"exp":     time.Now().Add(7 * 24 * time.Hour).Unix(),
		"iat":     time.Now().Unix(),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(s.jwtSecret))
}

