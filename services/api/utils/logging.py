"""
Logging utilities for Krakenly API
Provides request/response logging middleware and logger setup
"""
import json
import time
import logging

# Configure module logger
logger = logging.getLogger('api')


def setup_logging():
    """
    Configure logging for the application.
    Sets up format and level for the root logger.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logger


def get_logger():
    """Get the API logger instance"""
    return logger


def create_request_logger(app):
    """
    Create request/response logging middleware for Flask app.
    
    This adds before_request and after_request handlers that log
    incoming requests and outgoing responses with timing information.
    
    Args:
        app: Flask application instance
    """
    from flask import request, g
    import uuid
    
    @app.before_request
    def before_request():
        """Log incoming request and start timer"""
        g.start_time = time.time()
        
        # Get or generate activity ID
        g.activity_id = request.headers.get('X-Activity-ID') or str(uuid.uuid4())
        
        # Skip logging for health checks to reduce noise
        if request.path == '/health':
            return
        
        # Log request details
        log_data = {
            'activity_id': g.activity_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr
        }
        
        # Log request body for POST/PUT (truncated)
        if request.method in ['POST', 'PUT'] and request.is_json:
            try:
                body = request.get_json(silent=True) or {}
                # Truncate large fields for logging
                log_body = {}
                for k, v in body.items():
                    if isinstance(v, str) and len(v) > 200:
                        log_body[k] = v[:200] + f'... ({len(v)} chars)'
                    else:
                        log_body[k] = v
                log_data['body'] = log_body
            except Exception:
                pass
        
        logger.info(f"REQUEST: {json.dumps(log_data)}")

    @app.after_request
    def after_request(response):
        """Log response and timing"""
        # Add activity ID to response headers
        activity_id = g.get('activity_id')
        if activity_id:
            response.headers['X-Activity-ID'] = activity_id
        
        # Skip logging for health checks
        if request.path == '/health':
            return response
        
        duration = time.time() - g.get('start_time', time.time())
        
        log_data = {
            'activity_id': activity_id,
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': round(duration * 1000, 2)
        }
        
        # Log response body for API responses (truncated)
        if response.is_json:
            try:
                body = response.get_json(silent=True) or {}
                log_body = {}
                for k, v in body.items():
                    if isinstance(v, str) and len(v) > 300:
                        log_body[k] = v[:300] + f'... ({len(v)} chars)'
                    elif isinstance(v, list) and len(v) > 5:
                        log_body[k] = f'[{len(v)} items]'
                    else:
                        log_body[k] = v
                log_data['response'] = log_body
            except Exception:
                pass
        
        # Color code by duration
        if duration > 10:
            logger.warning(f"RESPONSE [SLOW]: {json.dumps(log_data)}")
        elif duration > 5:
            logger.info(f"RESPONSE [OK]: {json.dumps(log_data)}")
        else:
            logger.info(f"RESPONSE [FAST]: {json.dumps(log_data)}")
        
        return response
