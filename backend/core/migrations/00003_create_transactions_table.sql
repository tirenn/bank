-- +goose Up
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    type VARCHAR(32) NOT NULL,
    amount_cents BIGINT NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(64) NOT NULL,
    counterparty_account_num VARCHAR(32),
    counterparty_name VARCHAR(255),
    reference_number VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);


CREATE INDEX IF NOT EXISTS idx_transactions_account_id_created_at ON transactions(account_id, created_at DESC);

-- +goose Down
DROP TABLE IF EXISTS transactions;