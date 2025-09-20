-- Create additional indexes for better performance
CREATE INDEX IF NOT EXISTS idx_audit_model_name ON audit_logs(model_name);
CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_logs(status);
CREATE INDEX IF NOT EXISTS idx_audit_pii_redacted ON audit_logs(pii_redacted);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at);

-- Create a view for quick access to recent logs
CREATE OR REPLACE VIEW recent_audit_logs AS
SELECT 
    log_id,
    timestamp,
    event_type,
    user_id,
    model_name,
    status,
    duration_ms,
    pii_redacted
FROM audit_logs 
WHERE timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;

-- Create a function to get logs by user
CREATE OR REPLACE FUNCTION get_user_audit_logs(user_id_param VARCHAR)
RETURNS TABLE (
    log_id VARCHAR,
    timestamp TIMESTAMP,
    event_type VARCHAR,
    model_name VARCHAR,
    status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.log_id,
        al.timestamp,
        al.event_type,
        al.model_name,
        al.status
    FROM audit_logs al
    WHERE al.user_id = user_id_param
    ORDER BY al.timestamp DESC;
END;
$$ LANGUAGE plpgsql;