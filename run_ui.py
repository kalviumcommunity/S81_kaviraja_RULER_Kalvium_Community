"""
Launcher script for RULER Banking Regulatory AI Platform.
Starts the FastAPI Backend (Port 8000) and Next.js Dual Dashboard (Port 3000).

Routes:
- User Compliance Portal: http://localhost:3000/
- Admin Console:          http://localhost:3000/ruler
- Backend REST API:       http://127.0.0.1:8000/
"""

import sys
import os
import time
import subprocess
import uvicorn
import shutil

# Ensure project root and src are on python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def is_port_active(port):
    try:
        import urllib.request
        urllib.request.urlopen(f"http://localhost:{port}", timeout=1)
        return True
    except Exception:
        return False

def main():
    print("==================================================================")
    print("  * RULER - Banking Regulatory AI & Intelligence Platform")
    print("==================================================================")
    print("  - User Compliance Portal: http://localhost:3000/")
    print("  - Admin Console:          http://localhost:3000/ruler")
    print("  - Backend REST Services:  http://127.0.0.1:8000/")
    print("==================================================================")
    print("  Palette: Oxford Blue (#002147) & Warm Almond / Tan (#D2B48C)")
    print("  Admin Passkey: admin123  or  ruler2026")
    print("==================================================================\n")

    frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
    
    # Check if Next.js dev server is already running on port 3000
    if is_port_active(3000):
        print("✓ Next.js Frontend is already active on http://localhost:3000")
    else:
        print("Starting Next.js Frontend Server on port 3000...")
        npm_cmd = shutil.which("npm.cmd") or shutil.which("npm") or "npm"
        try:
            subprocess.Popen([npm_cmd, "run", "dev"], cwd=frontend_dir, shell=True)
            print("✓ Next.js Frontend dev server launched on http://localhost:3000")
            time.sleep(2)
        except Exception as e:
            print(f"Note: Could not auto-launch npm dev ({e}). Run 'cd frontend && npm run dev' separately.")

    print("\nStarting FastAPI Backend on http://127.0.0.1:8000 ...")
    uvicorn.run("src.server:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
