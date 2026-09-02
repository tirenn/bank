package domain

import (
	"time"
)


type User struct {
	ID                uint64     `gorm:"primaryKey;autoIncrement" json:"id"`
	Email             string     `gorm:"uniqueIndex;type:varchar(255);not null" json:"email"`
	PasswordHash      string     `gorm:"type:varchar(255);not null" json:"-"`
	FullName          string     `gorm:"type:varchar(255);not null" json:"full_name"`
	Role              string     `gorm:"type:varchar(32);not null" json:"role"`
	AddressStreet     string     `gorm:"type:varchar(255)" json:"address_street"`
	AddressCity       string     `gorm:"type:varchar(100)" json:"address_city"`
	AddressState      string     `gorm:"type:varchar(50)" json:"address_state"`
	AddressPostalCode string     `gorm:"type:varchar(20)" json:"address_postal_code"`
	AddressCountry    string     `gorm:"type:varchar(100)" json:"address_country"`
	PhoneNumber       string     `gorm:"type:varchar(50)" json:"phone_number"`
	KYCStatus         string     `gorm:"type:varchar(32)" json:"kyc_status"`
	KYCDocType        string     `gorm:"type:varchar(50)" json:"kyc_doc_type"`
	KYCDocNumber      string     `gorm:"type:varchar(100)" json:"kyc_doc_number"`
	KYCVerifiedAt     *time.Time `json:"kyc_verified_at"`
	CreatedAt         time.Time  `json:"created_at"`
}


func (User) TableName() string {
	return "users"
}

type RegisterRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required,min=6"`
	FullName string `json:"full_name" binding:"required"`
}

type LoginRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required"`
}

type AuthResponse struct {
	Token string `json:"token"`
	User  User   `json:"user"`
}

type UpdateAddressRequest struct {
	Street     string `json:"street" binding:"required"`
	City       string `json:"city" binding:"required"`
	State      string `json:"state" binding:"required"`
	PostalCode string `json:"postal_code" binding:"required"`
	Country    string `json:"country" binding:"required"`
}

type UpdateKYCRequest struct {
	DocType   string `json:"doc_type" binding:"required"`
	DocNumber string `json:"doc_number" binding:"required"`
}

