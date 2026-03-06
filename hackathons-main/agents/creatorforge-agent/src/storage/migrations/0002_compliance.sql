ALTER TABLE campaigns ADD COLUMN updated_at TEXT;
ALTER TABLE campaigns ADD COLUMN delivered_at TEXT;
ALTER TABLE campaigns ADD COLUMN rejected_at TEXT;
ALTER TABLE campaigns ADD COLUMN rejection_reason TEXT;

UPDATE campaigns
SET updated_at = COALESCE(updated_at, created_at)
WHERE updated_at IS NULL;

ALTER TABLE creative_assets ADD COLUMN provenance_json TEXT;

ALTER TABLE purchases ADD COLUMN idempotency_key TEXT;
ALTER TABLE purchases ADD COLUMN payer TEXT;
ALTER TABLE purchases ADD COLUMN tx_hash TEXT;
ALTER TABLE purchases ADD COLUMN payment_metadata_json TEXT;
ALTER TABLE purchases ADD COLUMN mindra_execution_id TEXT;

ALTER TABLE sales ADD COLUMN idempotency_key TEXT;
ALTER TABLE sales ADD COLUMN payer TEXT;
ALTER TABLE sales ADD COLUMN tx_hash TEXT;
ALTER TABLE sales ADD COLUMN credits_redeemed INTEGER;

ALTER TABLE approval_requests ADD COLUMN mindra_execution_id TEXT;
ALTER TABLE approval_requests ADD COLUMN mindra_approval_id TEXT;

ALTER TABLE audit_events ADD COLUMN idempotency_key TEXT;
ALTER TABLE ad_events ADD COLUMN idempotency_key TEXT;

ALTER TABLE procurement_decisions ADD COLUMN mindra_execution_id TEXT;
ALTER TABLE procurement_decisions ADD COLUMN mindra_approval_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_purchases_idempotency
ON purchases(idempotency_key)
WHERE idempotency_key IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_sales_idempotency
ON sales(idempotency_key)
WHERE idempotency_key IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_ad_events_idempotency
ON ad_events(idempotency_key)
WHERE idempotency_key IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_events_idempotency
ON audit_events(idempotency_key)
WHERE idempotency_key IS NOT NULL;
