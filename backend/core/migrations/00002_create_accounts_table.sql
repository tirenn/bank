-- +goose Up
CREATE TABLE IF NOT EXISTS accounts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_number VARCHAR(32) UNIQUE NOT NULL,
    balance_cents BIGINT NOT NULL CHECK (balance_cents >= 0),
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(16) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);


CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_accounts_account_number ON accounts(account_number);

-- +goose Down
DROP TABLE IF EXISTS accounts;