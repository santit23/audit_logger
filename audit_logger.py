import logging 
import json
import datetime
import uuid
from typing import Dict, Any, Optional
import psycopg2
from psycopg2 import sql
import hashlib

class AuditLogger:
    def __init__(self, db_config: Optional[Dict] = None, log_file: str = "audit.log"):
        """
        Initialize the audit logger
        
        Args:
            db_config: Database configuration for persistent storage
            log_file: File path for backup logging
        """

        self.logger = logging.getLogger('audit_logger')
        self.logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        self.db_config = db_config
        self.db_connection = None

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

        if db_config:
            self._setup_database()

    def _setup_database(self):
        """Initialize database connection and create audit table if not exists""" 

        try:
            self.db_connection = psycopg2.connect(**self.db_config)
            cursor = self.db_connection.cursor()

            create_table_query = """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                log_id VARCHAR(36) UNIQUE,
                timestamp TIMESTAMP NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                user_id VARCHAR(100),
                inference_id VARCHAR(100),
                model_name VARCHAR(100),
                input_hash VARCHAR(64),
                output_hash VARCHAR(64),
                status VARCHAR(20),
                duration_ms INTEGER,
                gpu_usage JSONB,
                ip_address VARCHAR(45),
                user_agent TEXT,
                metadata JSONB,
                pii_redacted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type);
            CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_inference_id ON audit_logs(inference_id);
            """

            cursor.execute(create_table_query)
            self.db_connection.commit()
            cursor.close()
            
            self.db_available = True
            self.logger.info("Database setup complete")


        except (Exception, psycopg2.Error) as e:
            self.logger.warning(f"⚠️ Database connection failed, using file logging only: {str(e)}")
            self.db_available = False

    def _hash_sensitive_data(self, data: Any) -> str:
        """Hash sensitive data using SHA-256"""
        if data is None:
            return None
        data_str = json.dumps(data, sort_keys=True) if isinstance(data, ((dict, list))) else str
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    def _redact_pii(self, data: Dict) -> Dict:
        """Redact PII from the log data"""
        redacted_data = data.copy()
        pii_fields = ['email', 'phone', 'address', 'name', 'ssn', 'credit_card', 'password']
        for field in pii_fields:
            if field in redacted_data:
                redacted_data[field] = '[REDACTED]'
        return redacted_data

    def log_event(self, event_type: str, data: Dict, user_id: Optional[str] = None):
        """
        Log an audit event
        
        Args:
            event_type: Type of event (e.g., 'inference_start', 'inference_complete')
            data: Event data
            user_id: User identifier (if available)
        """

        try:
            # Generate unique log ID
            log_id = str(uuid.uuid4())
            timestamp = datetime.datetime.utcnow()
            
            # Redact PII from metadata
            metadata = data.get('metadata', {})
            redacted_metadata = self._redact_pii(metadata)
            pii_redacted = metadata != redacted_metadata
            
            # Prepare log entry
            log_entry = {
                'log_id': log_id,
                'timestamp': timestamp.isoformat(),
                'event_type': event_type,
                'user_id': user_id,
                'inference_id': data.get('inference_id'),
                'model_name': data.get('model_name'),
                'input_hash': self._hash_sensitive_data(data.get('input')),
                'output_hash': self._hash_sensitive_data(data.get('output')),
                'status': data.get('status'),
                'duration_ms': data.get('duration_ms'),
                'gpu_usage': data.get('gpu_usage'),
                'ip_address': data.get('ip_address'),
                'user_agent': data.get('user_agent'),
                'metadata': redacted_metadata,
                'pii_redacted': pii_redacted
            }
            
            # Log to file
            self.logger.info(json.dumps(log_entry))
            
            # Store in database if configured
            if self.db_available and self.db_connection:
                self._store_in_database(log_entry)
                
        except Exception as e:
            self.logger.error(f"Failed to log event: {str(e)}")

    def _store_in_database(self, log_entry: Dict):
        """Store log entry in database"""
        try:
            cursor = self.db_connection.cursor()
            
            insert_query = """
            INSERT INTO audit_logs (
                log_id, timestamp, event_type, user_id, inference_id, model_name,
                input_hash, output_hash, status, duration_ms, gpu_usage,
                ip_address, user_agent, metadata, pii_redacted
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                log_entry['log_id'],
                log_entry['timestamp'],
                log_entry['event_type'],
                log_entry['user_id'],
                log_entry['inference_id'],
                log_entry['model_name'],
                log_entry['input_hash'],
                log_entry['output_hash'],
                log_entry['status'],
                log_entry['duration_ms'],
                json.dumps(log_entry['gpu_usage']) if log_entry['gpu_usage'] else None,
                log_entry['ip_address'],
                log_entry['user_agent'],
                json.dumps(log_entry['metadata']) if log_entry['metadata'] else None,
                log_entry['pii_redacted']
            ))
            
            self.db_connection.commit()
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"Database storage failed: {str(e)}")
    
    def close(self):
        """Clean up resources"""
        if self.db_connection:
            self.db_connection.close()