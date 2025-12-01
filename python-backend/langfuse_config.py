"""
Centralized Langfuse configuration and client initialization.

This module provides:
- Production-ready Langfuse client with proper configuration
- Sampling and filtering support
- Non-blocking auth check
- Shutdown/flush logic
- Environment-based configuration
"""

import os
import atexit
import threading
from typing import Optional
from langfuse import Langfuse
from langfuse.decorators import langfuse_context


# Global Langfuse client instance
_langfuse_client: Optional[Langfuse] = None
_langfuse_lock = threading.Lock()


def get_langfuse_client() -> Optional[Langfuse]:
    """
    Get or create the global Langfuse client instance.
    
    Returns:
        Langfuse client instance, or None if credentials are not configured
    """
    global _langfuse_client
    
    if _langfuse_client is not None:
        return _langfuse_client
    
    with _langfuse_lock:
        # Double-check pattern
        if _langfuse_client is not None:
            return _langfuse_client
        
        # Check if credentials are available
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        
        if not secret_key or not public_key:
            print("[LANGFUSE] Credentials not configured - tracing disabled")
            return None
        
        # Get configuration from environment
        base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
        environment = os.getenv("ENVIRONMENT", os.getenv("ENV", "development"))
        sample_rate = float(os.getenv("LANGFUSE_SAMPLE_RATE", "1.0"))  # Default: 100% sampling
        
        # Initialize Langfuse client
        try:
            _langfuse_client = Langfuse(
                secret_key=secret_key,
                public_key=public_key,
                host=base_url,
                enabled=os.getenv("LANGFUSE_ENABLED", "true").lower() == "true",
            )
            
            print("[LANGFUSE] Initialized with config:")
            print(f"  - Base URL: {base_url}")
            print(f"  - Environment: {environment}")
            print(f"  - Sample Rate: {sample_rate * 100:.1f}%")
            print(f"  - Enabled: {_langfuse_client.enabled}")
            print(f"  - Secret Key: {'Set' if secret_key else 'NOT SET'}")
            print(f"  - Public Key: {'Set' if public_key else 'NOT SET'}")
            
            # Perform non-blocking auth check in background thread
            def auth_check_async():
                try:
                    # Test that the client can be used by creating a test trace
                    # This will fail fast if credentials are invalid
                    test_trace = _langfuse_client.trace(name="health-check", user_id="system")
                    test_trace.update(output={"status": "ok"})
                    _langfuse_client.flush()
                    print("[LANGFUSE] ✓ Client initialized and verified successfully")
                except Exception as e:
                    print(f"[LANGFUSE] ⚠️  Warning: Auth check failed: {e}")
                    print(f"[LANGFUSE] ⚠️  Tracing may not work. Check your credentials.")
            
            # Run auth check in background to avoid blocking startup
            auth_thread = threading.Thread(target=auth_check_async, daemon=True)
            auth_thread.start()
            
            # Register shutdown handler
            atexit.register(shutdown_langfuse)
            
        except Exception as e:
            print(f"[LANGFUSE] ✗ Error initializing client: {e}")
            print(f"[LANGFUSE] ✗ Tracing will be disabled. Check your LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY environment variables.")
            _langfuse_client = None
        
        return _langfuse_client


def should_sample() -> bool:
    """
    Determine if current request should be sampled based on sample rate.
    
    Returns:
        True if request should be traced, False otherwise
    """
    import random
    
    sample_rate = float(os.getenv("LANGFUSE_SAMPLE_RATE", "1.0"))
    return random.random() < sample_rate


def get_trace_metadata(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    flow_name: Optional[str] = None,
    **kwargs
) -> dict:
    """
    Build standardized trace metadata.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        flow_name: Name of the flow/journey
        **kwargs: Additional metadata to include
        
    Returns:
        Dictionary of metadata
    """
    metadata = {
        "environment": os.getenv("ENVIRONMENT", os.getenv("ENV", "development")),
        "version": os.getenv("APP_VERSION", "2.0.0"),
    }
    
    if user_id:
        metadata["user_id"] = user_id
    if session_id:
        metadata["session_id"] = session_id
    if flow_name:
        metadata["flow_name"] = flow_name
    
    # Add any additional metadata
    metadata.update(kwargs)
    
    return metadata


def shutdown_langfuse():
    """
    Shutdown Langfuse client and flush all pending traces.
    Should be called on application termination.
    """
    global _langfuse_client
    
    if _langfuse_client is not None:
        try:
            print("[LANGFUSE] Shutting down and flushing traces...")
            _langfuse_client.flush()
            print("[LANGFUSE] ✓ Shutdown complete")
        except Exception as e:
            print(f"[LANGFUSE] ⚠️  Error during shutdown: {e}")


def flush_langfuse():
    """
    Flush pending traces to Langfuse.
    Can be called periodically or before important operations.
    """
    global _langfuse_client
    
    if _langfuse_client is not None:
        try:
            _langfuse_client.flush()
        except Exception as e:
            print(f"[LANGFUSE] ⚠️  Error flushing traces: {e}")

