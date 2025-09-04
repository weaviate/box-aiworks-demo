#!/usr/bin/env python3
"""
Main entry point for Railway deployment
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        import uvicorn
        from app import app
        
        port_str = os.environ.get("PORT")
        print(f"PORT environment variable: {port_str}")
        
        # Use Railway's PORT if available, otherwise use 8000
        if port_str:
            port = int(port_str)
        else:
            port = 8000
            print("WARNING: PORT environment variable not set, using port 8000")
        
        # Force port to 8000 since Railway is configured for this port
        port = 8000
        print(f"Using port 8000 (Railway configured port)")
        
        print(f"Starting server on port {port}")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except ImportError as e:
        print(f"Import error: {e}")
        print("Available packages:")
        import pkg_resources
        for package in pkg_resources.working_set:
            print(f"  {package.project_name}=={package.version}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
