-- +goose Up
-- +goose StatementBegin
ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS account_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS account_type VARCHAR(32),
ADD COLUMN IF NOT EXISTS card_number VARCHAR(32),
ADD COLUMN IF NOT EXISTS card_brand VARCHAR(32),
ADD COLUMN IF NOT EXISTS card_expiry VARCHAR(10),
ADD COLUMN IF NOT EXISTS card_cvv VARCHAR(4);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
ALTER TABLE accounts
DROP COLUMN IF EXISTS account_name,
DROP COLUMN IF EXISTS account_type,
DROP COLUMN IF EXISTS card_number,
DROP COLUMN IF EXISTS card_brand,
DROP COLUMN IF EXISTS card_expiry,
DROP COLUMN IF EXISTS card_cvv;
-- +goose StatementEnd
