# main.py
import time
import random
from datetime import datetime
from audit_logger import AuditLogger

# Database configuration (modify with your actual credentials)
DATABASE_CONFIG = {
    'dbname': 'audit_db',
    'user': 'audit_user',
    'password': 'secure_password123',
    'host': 'localhost',
    'port': '5432'
}

# Event types for consistent logging
AUDIT_EVENTS = {
    'INFERENCE_START': 'inference_start',
    'INFERENCE_COMPLETE': 'inference_complete',
    'INFERENCE_ERROR': 'inference_error',
    'MODEL_LOAD': 'model_load',
    'MODEL_UNLOAD': 'model_unload',
    'USER_AUTH': 'user_authentication',
    'ACCESS_DENIED': 'access_denied',
    'GPU_ALLOCATION': 'gpu_allocation',
    'GPU_RELEASE': 'gpu_release'
}

class MockGPUInferenceService:
    def __init__(self):
        self.audit_logger = AuditLogger(db_config=DATABASE_CONFIG, log_file='gpu_audit.log')
        self.loaded_models = {}
        print(" Audit Logger initialized with database and file logging")
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Mock user authentication"""
        success = password == "correct_password"  # Simple mock check
        
        audit_data = {
            'auth_method': 'password',
            'success': success,
            'client_version': '1.2.0',
            'metadata': {
                'username': username,
                'auth_attempt_time': datetime.utcnow().isoformat()
            }
        }
        
        event_type = AUDIT_EVENTS['USER_AUTH'] if success else AUDIT_EVENTS['ACCESS_DENIED']
        self.audit_logger.log_event(event_type, audit_data, user_id=username)
        
        return success
    
    def load_model(self, model_name: str, user_id: str):
        """Mock model loading process"""
        print(f"📦 Loading model: {model_name}")
        
        if model_name in self.loaded_models:
            print(f"⚠️  Model {model_name} already loaded")
            return True
        
        # Simulate loading time
        time.sleep(0.5)
        self.loaded_models[model_name] = {
            'loaded_at': datetime.utcnow(),
            'loaded_by': user_id
        }
        
        audit_data = {
            'model_name': model_name,
            'model_size_gb': 2.5,
            'load_time_seconds': 0.5,
            'gpu_memory_required': 4096,
            'metadata': {
                'framework': 'TensorRT',
                'precision': 'FP16',
                'user_email': f"{user_id}@company.com"  # Will be redacted
            }
        }
        
        self.audit_logger.log_event(AUDIT_EVENTS['MODEL_LOAD'], audit_data, user_id)
        print(f" Model {model_name} loaded successfully")
        return True
    
    def run_inference(self, model_name: str, input_data: dict, user_id: str):
        """Mock inference execution"""
        if model_name not in self.loaded_models:
            print(f" Model {model_name} not loaded")
            return None
        
        inference_id = f"inf_{int(time.time())}_{random.randint(1000, 9999)}"
        print(f"Starting inference {inference_id} with model {model_name}")
        
        # Log inference start
        start_audit_data = {
            'inference_id': inference_id,
            'model_name': model_name,
            'input': input_data,
            'batch_size': 1,
            'metadata': {
                'user_email': f"{user_id}@company.com",  # Will be redacted
                'request_id': f"req_{random.randint(10000, 99999)}"
            }
        }
        self.audit_logger.log_event(AUDIT_EVENTS['INFERENCE_START'], start_audit_data, user_id)
        
        # Simulate GPU inference processing
        start_time = time.time()
        time.sleep(random.uniform(0.1, 0.3))  # Random processing time
        
        # Simulate occasional errors
        if random.random() < 0.1:  # 10% chance of error
            error_audit_data = {
                'inference_id': inference_id,
                'model_name': model_name,
                'error_message': 'GPU memory allocation failed',
                'error_code': 'GPU_OOM',
                'duration_ms': int((time.time() - start_time) * 1000),
                'gpu_usage': {
                    'gpu_utilization': 95,
                    'memory_used_mb': 4096,
                    'temperature_c': 78,
                    'power_draw_w': 250
                },
                'metadata': {
                    'retry_count': 0,
                    'error_timestamp': datetime.utcnow().isoformat()
                }
            }
            self.audit_logger.log_event(AUDIT_EVENTS['INFERENCE_ERROR'], error_audit_data, user_id)
            print(f" Inference {inference_id} failed")
            return None
        
        # Successful inference
        processing_time_ms = int((time.time() - start_time) * 1000)
        output_data = {
            'predictions': [
                {'class': 'cat', 'confidence': 0.92},
                {'class': 'dog', 'confidence': 0.07}
            ],
            'processing_time_ms': processing_time_ms
        }
        
        # Log inference completion
        complete_audit_data = {
            'inference_id': inference_id,
            'model_name': model_name,
            'input': input_data,
            'output': output_data,
            'status': 'success',
            'duration_ms': processing_time_ms,
            'gpu_usage': {
                'gpu_utilization': random.randint(70, 95),
                'memory_used_mb': random.randint(2048, 4096),
                'temperature_c': random.randint(65, 75),
                'power_draw_w': random.randint(200, 300)
            },
            'ip_address': f"192.168.1.{random.randint(1, 255)}",
            'user_agent': 'Python-Inference-Client/2.1.0',
            'metadata': {
                'batch_processing': False,
                'quality_of_service': 'high_priority'
            }
        }
        
        self.audit_logger.log_event(AUDIT_EVENTS['INFERENCE_COMPLETE'], complete_audit_data, user_id)
        print(f"Inference {inference_id} completed in {processing_time_ms}ms")
        return output_data
    
    def unload_model(self, model_name: str, user_id: str):
        """Mock model unloading"""
        if model_name not in self.loaded_models:
            print(f"⚠️  Model {model_name} not loaded")
            return False
        
        del self.loaded_models[model_name]
        
        audit_data = {
            'model_name': model_name,
            'memory_freed_mb': 4096,
            'unload_reason': 'manual',
            'metadata': {
                'unload_initiated_by': user_id,
                'session_duration_minutes': random.randint(5, 120)
            }
        }
        
        self.audit_logger.log_event(AUDIT_EVENTS['MODEL_UNLOAD'], audit_data, user_id)
        print(f"📤 Model {model_name} unloaded")
        return True
    
    def cleanup(self):
        """Clean up resources"""
        self.audit_logger.close()
        print("🧹 Resources cleaned up")

def simulate_workload(service: MockGPUInferenceService):
    """Simulate a realistic workload with multiple users and models"""
    
    users = ['alice', 'bob', 'charlie', 'diana']
    models = ['resnet-50', 'yolov4', 'bert-large', 'gpt-3']
    
    print("\n" + "="*60)
    print(" SIMULATING GPU INFERENCE WORKLOAD")
    print("="*60)
    
    # Simulate user authentications
    for user in users:
        success = service.authenticate_user(user, "correct_password")
        if success:
            print(f"🔓 User {user} authenticated successfully")
        else:
            print(f"🔒 User {user} authentication failed")
    
    print("\n" + "-"*40)
    
    # Load models
    for model in models:
        user = random.choice(users)
        service.load_model(model, user)
    
    print("\n" + "-"*40)
    
    # Run multiple inferences
    for i in range(20):
        user = random.choice(users)
        model = random.choice(models)
        
        input_data = {
            'data': f'sample_input_{i}',
            'format': 'image' if 'resnet' in model or 'yolo' in model else 'text',
            'size_kb': random.randint(100, 5000)
        }
        
        result = service.run_inference(model, input_data, user)
        
        # Occasionally unload and reload models
        if i % 7 == 0 and random.random() < 0.3:
            model_to_unload = random.choice(models)
            service.unload_model(model_to_unload, user)
            time.sleep(0.2)
            service.load_model(model_to_unload, user)
    
    print("\n" + "-"*40)
    
    # Unload all models
    for model in models[:]:  # Copy list to avoid modification during iteration
        if model in service.loaded_models:
            user = random.choice(users)
            service.unload_model(model, user)

def main():
    """Main function to run the audit logging demonstration"""
    
    print(" GPU Inference Audit Logger Demo")
    print(" Logs will be saved to 'gpu_audit.log' and PostgreSQL database")
    print(" PII redaction and data hashing will be applied automatically")
    print()
    
    try:
        # Initialize the service
        service = MockGPUInferenceService()
        
        # Run the simulation
        simulate_workload(service)
        
        # Clean up
        service.cleanup()
        
        print("\n" + "="*60)
        print(" Simulation completed successfully!")
        print(" Check the following for audit logs:")
        print("   - File: gpu_audit.log")
        print("   - Database: audit_logs table")
        print("   - Look for PII redaction markers: [REDACTED]")
        print("   - Notice hashed input/output data for privacy")
        print("="*60)
        
    except Exception as e:
        print(f" Error during simulation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()