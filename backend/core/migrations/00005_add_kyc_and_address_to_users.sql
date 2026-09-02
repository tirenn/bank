-- +goose Up
-- +goose StatementBegin
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS address_street VARCHAR(255),
ADD COLUMN IF NOT EXISTS address_city VARCHAR(100),
ADD COLUMN IF NOT EXISTS address_state VARCHAR(50),
ADD COLUMN IF NOT EXISTS address_postal_code VARCHAR(20),
ADD COLUMN IF NOT EXISTS address_country VARCHAR(100),
ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50),
ADD COLUMN IF NOT EXISTS kyc_status VARCHAR(32),
ADD COLUMN IF NOT EXISTS kyc_doc_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS kyc_doc_number VARCHAR(100),
ADD COLUMN IF NOT EXISTS kyc_verified_at TIMESTAMP WITH TIME ZONE;
-- +goose StatementEnd


-- +goose Down
-- +goose StatementBegin
ALTER TABLE users 
DROP COLUMN IF EXISTS address_street,
DROP COLUMN IF EXISTS address_city,
DROP COLUMN IF EXISTS address_state,
DROP COLUMN IF EXISTS address_postal_code,
DROP COLUMN IF EXISTS address_country,
DROP COLUMN IF EXISTS phone_number,
DROP COLUMN IF EXISTS kyc_status,
DROP COLUMN IF EXISTS kyc_doc_type,
DROP COLUMN IF EXISTS kyc_doc_number,
DROP COLUMN IF EXISTS kyc_verified_at;
-- +goose StatementEnd
