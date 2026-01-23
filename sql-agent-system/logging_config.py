# logging_config.py
import logging
import sys
from datetime import datetime
import os

def setup_logging(log_level=logging.INFO):
    """
    Configure production-grade logging with:
    - Console output for development
    - File output for production
    - Structured format with timestamps
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Generate log filename with timestamp
    log_filename = os.path.join(log_dir, f"sql_agent_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Define log format
    log_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # File handler (rotating)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)
    
    logging.info("="*80)
    logging.info(f"SQL Agent System Initialized - Log file: {log_filename}")
    logging.info("="*80)
    
    return root_logger
