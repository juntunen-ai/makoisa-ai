# Main entry point for Cloud Run deployment
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Set up environment
os.environ.setdefault('STREAMLIT_SERVER_PORT', '8080')
os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
os.environ.setdefault('STREAMLIT_BROWSER_GATHER_USAGE_STATS', 'false')
os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')

if __name__ == "__main__":
    import subprocess
    import sys
    
    # Run the Streamlit app
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "ui/app.py",
        "--server.port=8080",
        "--server.address=0.0.0.0", 
        "--server.headless=true"
    ])
