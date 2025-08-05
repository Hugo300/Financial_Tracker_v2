#!/usr/bin/env python3
"""
Financial Tracker Application Entry Point

This module provides the main entry point for the Financial Tracker application.
It creates and runs the Flask application with proper configuration.
"""

import os
import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from src.config import get_config
from src.web.app import create_app


def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('financial_tracker.log')
        ]
    )


def main():
    """Main entry point for the application."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Get configuration from environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    
    try:
        # Create Flask application
        app = create_app(config_name)

        print(config_name)
        
        # Get host and port from environment or use defaults
        config = get_config(config_name)
        os.environ["FLASK_HOST"] = str(config.FLASK_HOST)
        os.environ["FLASK_PORT"] = str(config.FLASK_PORT)

        host = os.environ.get('FLASK_HOST', '127.0.0.1')
        port = int(os.environ.get('FLASK_PORT', 5000))
        debug = config_name == 'development'
        
        logger.info(f"Starting Financial Tracker on {host}:{port}")
        logger.info(f"Configuration: {config_name}")
        logger.info(f"Debug mode: {debug}")
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
