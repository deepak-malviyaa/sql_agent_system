# launcher.py
"""
Unified Launcher for SQL Agent System
Provides multiple interface options: CLI, UI, MCP Server, API
"""

import argparse
import sys
import os

def launch_cli():
    """Launch CLI interface"""
    print("🚀 Launching CLI interface...")
    import main
    # main.py already has the CLI loop

def launch_ui(share=False, port=7860):
    """Launch Gradio web UI"""
    print(f"🎨 Launching Web UI on port {port}...")
    from ui.gradio_app import launch_ui as gradio_launch
    gradio_launch(share=share, server_port=port)

def launch_mcp():
    """Launch MCP server"""
    print("🔌 Launching MCP Server...")
    from mcp_server import start_mcp_server
    start_mcp_server()

def launch_api(host="0.0.0.0", port=8000):
    """Launch FastAPI REST API"""
    print(f"🌐 Launching REST API on {host}:{port}...")
    from api_server import app
    import uvicorn
    uvicorn.run(app, host=host, port=port)

def main():
    parser = argparse.ArgumentParser(
        description="SQL Agent System - Multiple Interface Options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launcher.py cli                    # CLI interface (default)
  python launcher.py ui                     # Web UI on localhost:7860
  python launcher.py ui --share             # Web UI with public URL
  python launcher.py ui --port 8080         # Web UI on custom port
  python launcher.py mcp                    # MCP server for agent-to-agent
  python launcher.py api                    # REST API on localhost:8000
  python launcher.py api --port 9000        # REST API on custom port
        """
    )
    
    parser.add_argument(
        'interface',
        choices=['cli', 'ui', 'mcp', 'api'],
        default='cli',
        nargs='?',
        help='Interface type to launch (default: cli)'
    )
    
    parser.add_argument(
        '--share',
        action='store_true',
        help='Create public Gradio URL (UI only)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        help='Port number (UI: default 7860, API: default 8000)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host address for API server (default: 0.0.0.0)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    from logging_config import setup_logging
    import logging
    setup_logging(logging.INFO)
    
    # Route to appropriate interface
    if args.interface == 'cli':
        launch_cli()
    
    elif args.interface == 'ui':
        port = args.port or 7860
        launch_ui(share=args.share, port=port)
    
    elif args.interface == 'mcp':
        launch_mcp()
    
    elif args.interface == 'api':
        port = args.port or 8000
        launch_api(host=args.host, port=port)

if __name__ == "__main__":
    main()
