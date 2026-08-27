CREATE TABLE IF NOT EXISTS agent_conversations (
    conversation_id UUID PRIMARY KEY,
    owner_id VARCHAR(120) NOT NULL,
    semantic_context JSONB NOT NULL DEFAULT '{}'::JSONB,
    turn_count INTEGER NOT NULL DEFAULT 0 CHECK (turn_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    CHECK (expires_at > created_at)
);

CREATE INDEX IF NOT EXISTS idx_agent_conversations_owner_last_seen
ON agent_conversations(owner_id, last_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_conversations_expiry
ON agent_conversations(expires_at);

COMMENT ON COLUMN agent_conversations.semantic_context IS
'Bounded routing metadata only; never raw prompts, generated answers or environmental values.';
