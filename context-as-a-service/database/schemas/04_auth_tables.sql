-- Authentication and API Key Management Schema
-- For Context-as-a-Service standalone authentication

-- Create auth schema if not exists
CREATE SCHEMA IF NOT EXISTS auth;

-- =====================================================
-- API KEYS TABLE
-- =====================================================

-- API Keys for accessing the Context-as-a-Service
CREATE TABLE IF NOT EXISTS auth.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL, -- SHA256 hash of the actual key
    tenant_id UUID REFERENCES rag.tenants(id) ON DELETE CASCADE,
    permissions TEXT[] DEFAULT ARRAY['read'], -- read, write, admin
    rate_limit_per_hour INTEGER DEFAULT 1000,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast key lookup
CREATE INDEX idx_api_keys_hash ON auth.api_keys(key_hash);
CREATE INDEX idx_api_keys_tenant ON auth.api_keys(tenant_id);

-- =====================================================
-- API KEY USAGE TRACKING
-- =====================================================

-- Track API key usage for rate limiting and analytics
CREATE TABLE IF NOT EXISTS auth.api_key_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID NOT NULL REFERENCES auth.api_keys(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    ip_address INET,
    user_agent TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for usage analytics
CREATE INDEX idx_api_key_usage_key_time ON auth.api_key_usage(api_key_id, created_at DESC);
CREATE INDEX idx_api_key_usage_endpoint ON auth.api_key_usage(endpoint, created_at DESC);

-- =====================================================
-- TENANT USERS (Optional - for future web UI)
-- =====================================================

-- Users within tenants (for future web interface)
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES rag.tenants(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'viewer' CHECK (role IN ('viewer', 'editor', 'admin', 'owner')),
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_tenant ON auth.users(tenant_id);
CREATE INDEX idx_users_email ON auth.users(email);

-- =====================================================
-- AUDIT LOG
-- =====================================================

-- Audit log for all authentication events
CREATE TABLE IF NOT EXISTS auth.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES rag.tenants(id) ON DELETE SET NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    api_key_id UUID REFERENCES auth.api_keys(id) ON DELETE SET NULL,
    action TEXT NOT NULL, -- login, logout, key_created, key_revoked, etc
    resource_type TEXT,
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_tenant_time ON auth.audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_audit_log_user_time ON auth.audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_log_action ON auth.audit_log(action, created_at DESC);

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to validate API key and get permissions
CREATE OR REPLACE FUNCTION auth.validate_api_key(key_hash TEXT)
RETURNS TABLE (
    api_key_id UUID,
    tenant_id UUID,
    permissions TEXT[],
    rate_limit_per_hour INTEGER,
    is_valid BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ak.id,
        ak.tenant_id,
        ak.permissions,
        ak.rate_limit_per_hour,
        (ak.is_active AND (ak.expires_at IS NULL OR ak.expires_at > NOW())) as is_valid
    FROM auth.api_keys ak
    WHERE ak.key_hash = validate_api_key.key_hash
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to track API usage
CREATE OR REPLACE FUNCTION auth.track_api_usage(
    p_api_key_id UUID,
    p_endpoint TEXT,
    p_method TEXT,
    p_status_code INTEGER,
    p_response_time_ms INTEGER,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    usage_id UUID;
BEGIN
    -- Insert usage record
    INSERT INTO auth.api_key_usage (
        api_key_id, endpoint, method, status_code,
        response_time_ms, ip_address, user_agent
    ) VALUES (
        p_api_key_id, p_endpoint, p_method, p_status_code,
        p_response_time_ms, p_ip_address, p_user_agent
    ) RETURNING id INTO usage_id;

    -- Update last used timestamp
    UPDATE auth.api_keys
    SET last_used_at = NOW()
    WHERE id = p_api_key_id;

    RETURN usage_id;
END;
$$ LANGUAGE plpgsql;

-- Function to check rate limits
CREATE OR REPLACE FUNCTION auth.check_rate_limit(p_api_key_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    usage_count INTEGER;
    rate_limit INTEGER;
BEGIN
    -- Get the rate limit for this key
    SELECT ak.rate_limit_per_hour INTO rate_limit
    FROM auth.api_keys ak
    WHERE ak.id = p_api_key_id;

    -- Count usage in the last hour
    SELECT COUNT(*) INTO usage_count
    FROM auth.api_key_usage
    WHERE api_key_id = p_api_key_id
    AND created_at > NOW() - INTERVAL '1 hour';

    RETURN usage_count < rate_limit;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS on all auth tables
ALTER TABLE auth.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.api_key_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.audit_log ENABLE ROW LEVEL SECURITY;

-- RLS Policies will be created based on your authentication strategy

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION auth.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_api_keys_updated_at
    BEFORE UPDATE ON auth.api_keys
    FOR EACH ROW
    EXECUTE FUNCTION auth.update_updated_at();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION auth.update_updated_at();
