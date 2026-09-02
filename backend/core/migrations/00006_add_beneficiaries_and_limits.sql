-- +goose Up
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS beneficiaries (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    nickname VARCHAR(100) NOT NULL,
    account_number VARCHAR(32) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);


CREATE INDEX IF NOT EXISTS idx_beneficiaries_user_id ON beneficiaries(user_id);

ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS daily_transfer_limit_cents BIGINT,
ADD COLUMN IF NOT EXISTS is_frozen BOOLEAN;

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS beneficiaries;
ALTER TABLE accounts
DROP COLUMN IF EXISTS daily_transfer_limit_cents,
DROP COLUMN IF EXISTS is_frozen;
-- +goose StatementEnd
