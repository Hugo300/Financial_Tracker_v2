#!/usr/bin/env python3
"""
Simple run script for Financial Tracker development.

This script provides a convenient way to run the application with different
configurations and options.
"""

import os
import sys
import argparse
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))


def run_app(host='127.0.0.1', port=5000, debug=True, config='development'):
    """Run the Flask application."""
    from src.web.app import create_app
    
    # Set environment variables
    os.environ['FLASK_ENV'] = config
    
    # Create and run app
    app = create_app(config)
    
    print(f"Starting Financial Tracker...")
    print(f"Configuration: {config}")
    print(f"Debug mode: {debug}")
    print(f"Server: http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    print("-" * 40)
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")


def run_tests(coverage=False, verbose=False):
    """Run the test suite."""
    import subprocess
    
    cmd = ['python', '-m', 'pytest']
    
    if coverage:
        cmd.extend(['--cov=src', '--cov-report=html', '--cov-report=term-missing'])
    
    if verbose:
        cmd.append('-v')
    
    print("Running test suite...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 40)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\nTests completed successfully!")
        if coverage:
            print("Coverage report generated in htmlcov/index.html")
    except subprocess.CalledProcessError as e:
        print(f"\nTests failed with exit code {e.returncode}")
        sys.exit(e.returncode)


def format_code():
    """Format code with Black."""
    import subprocess
    
    print("Formatting code with Black...")
    
    try:
        subprocess.run(['python', '-m', 'black', 'src/', 'tests/', '--check'], check=True)
        print("Code is already formatted correctly!")
    except subprocess.CalledProcessError:
        print("Formatting code...")
        subprocess.run(['python', '-m', 'black', 'src/', 'tests/'], check=True)
        print("Code formatted successfully!")


def lint_code():
    """Lint code with Flake8."""
    import subprocess
    
    print("Linting code with Flake8...")
    
    try:
        subprocess.run(['python', '-m', 'flake8', 'src/', 'tests/'], check=True)
        print("No linting errors found!")
    except subprocess.CalledProcessError as e:
        print(f"Linting failed with exit code {e.returncode}")
        sys.exit(e.returncode)


def setup_dev():
    """Set up development environment with sample data."""
    print("Setting up development environment...")
    
    try:
        import setup_dev
        setup_dev.setup_development_environment()
    except Exception as e:
        print(f"Failed to set up development environment: {e}")
        sys.exit(1)


def main():
    """Main entry point for the run script."""
    parser = argparse.ArgumentParser(description='Financial Tracker Development Tools')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run server command
    run_parser = subparsers.add_parser('run', help='Run the Flask application')
    run_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    run_parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    run_parser.add_argument('--no-debug', action='store_true', help='Disable debug mode')
    run_parser.add_argument('--config', default='development', 
                           choices=['development', 'testing', 'production'],
                           help='Configuration to use (default: development)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run the test suite')
    test_parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    test_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Code quality commands
    subparsers.add_parser('format', help='Format code with Black')
    subparsers.add_parser('lint', help='Lint code with Flake8')
    subparsers.add_parser('setup-dev', help='Set up development environment with sample data')
    
    # Quality command (format + lint + test)
    quality_parser = subparsers.add_parser('quality', help='Run all code quality checks')
    quality_parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        run_app(
            host=args.host,
            port=args.port,
            debug=not args.no_debug,
            config=args.config
        )
    elif args.command == 'test':
        run_tests(coverage=args.coverage, verbose=args.verbose)
    elif args.command == 'format':
        format_code()
    elif args.command == 'lint':
        lint_code()
    elif args.command == 'setup-dev':
        setup_dev()
    elif args.command == 'quality':
        print("Running all code quality checks...")
        print("=" * 50)
        format_code()
        print("\n" + "=" * 50)
        lint_code()
        print("\n" + "=" * 50)
        run_tests(coverage=args.coverage)
        print("\n" + "=" * 50)
        print("All quality checks passed!")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
