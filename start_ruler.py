#!/usr/bin/env python
"""
RULER RAG Platform - Startup Manager
Starts both backend API and Streamlit frontend with proper error handling
"""

import subprocess
import sys
import time
import os
import signal
from typing import Optional

class StartupManager:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
    
    def print_banner(self):
        """Print startup banner"""
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                     ⚖️  RULER RAG Platform                           ║
║                  Banking Regulatory Intelligence                     ║
║                                                                      ║
║  Starting up components...                                          ║
╚══════════════════════════════════════════════════════════════════════╝
        """)
    
    def check_environment(self):
        """Check if Python environment is properly configured"""
        print("✅ Checking environment...")
        
        # Check Python version
        if sys.version_info < (3, 10):
            print(f"❌ Python 3.10+ required (found {sys.version_info.major}.{sys.version_info.minor})")
            return False
        
        # Check .env file
        if not os.path.exists(".env"):
            print("⚠️  Warning: .env file not found")
            print("   Please create .env with: OPENAI_API_KEY=your_key_here")
            print("   Some features may not work without API key")
        
        print("✅ Environment check passed\n")
        return True
    
    def start_backend(self):
        """Start FastAPI backend server"""
        print("🚀 Starting Backend API (FastAPI)...")
        print("   URL: http://127.0.0.1:8000")
        print("   Docs: http://127.0.0.1:8000/docs")
        
        try:
            self.backend_process = subprocess.Popen(
                [sys.executable, "run_ui.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Wait for backend to start
            time.sleep(3)
            
            if self.backend_process.poll() is None:
                print("✅ Backend API started successfully\n")
                return True
            else:
                stdout, stderr = self.backend_process.communicate()
                print(f"❌ Backend failed to start:")
                print(f"   Error: {stderr or 'Unknown error'}\n")
                return False
        
        except FileNotFoundError:
            print("❌ Could not find run_ui.py")
            print("   Make sure you're in the project root directory\n")
            return False
        except Exception as e:
            print(f"❌ Error starting backend: {e}\n")
            return False
    
    def start_frontend(self):
        """Start Streamlit frontend"""
        print("🎨 Starting Streamlit Frontend...")
        print("   URL: http://127.0.0.1:8501")
        print("   Browser will open automatically\n")
        
        try:
            self.frontend_process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--logger.level=warning"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Wait for frontend to start
            time.sleep(3)
            
            if self.frontend_process.poll() is None:
                print("✅ Streamlit Frontend started successfully\n")
                return True
            else:
                stdout, stderr = self.frontend_process.communicate()
                print(f"❌ Frontend failed to start:")
                print(f"   Error: {stderr or 'Unknown error'}\n")
                return False
        
        except FileNotFoundError:
            print("❌ Streamlit not found. Install with:")
            print("   pip install streamlit\n")
            return False
        except Exception as e:
            print(f"❌ Error starting frontend: {e}\n")
            return False
    
    def print_startup_success(self):
        """Print successful startup message"""
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                   ✅ RULER Platform is Ready!                       ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  🌐 Frontend:  http://127.0.0.1:8501                                ║
║  🔌 Backend:   http://127.0.0.1:8000                                ║
║  📖 API Docs:  http://127.0.0.1:8000/docs                           ║
║                                                                      ║
║  ℹ️  Ctrl+C to stop all services                                     ║
║                                                                      ║
║  To test the implementation:                                        ║
║  • Open http://127.0.0.1:8501 in your browser                      ║
║  • Ask: "What are AML requirements?"                                ║
║  • Check that sources appear below the answer                       ║
║                                                                      ║
║  To run automated tests:                                            ║
║  • Open a new terminal                                              ║
║  • Run: python test_rag_implementation.py                           ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
        """)
    
    def print_startup_failed(self):
        """Print startup failure message"""
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                  ❌ Startup Failed                                   ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Troubleshooting:                                                   ║
║                                                                      ║
║  1. Ensure Python 3.10+ is installed:                               ║
║     python --version                                                ║
║                                                                      ║
║  2. Install dependencies:                                           ║
║     pip install -r requirements.txt                                 ║
║                                                                      ║
║  3. Set environment variables:                                      ║
║     Create .env file with OPENAI_API_KEY=your_key                 ║
║                                                                      ║
║  4. Check ports are available:                                      ║
║     Port 8000 (API) and 8501 (Streamlit) should be free            ║
║                                                                      ║
║  5. View detailed logs:                                             ║
║     Run python run_ui.py in one terminal                           ║
║     Run streamlit run streamlit_app.py in another                  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
        """)
    
    def setup_signal_handlers(self):
        """Setup handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print("\n\n🛑 Shutting down RULER Platform...")
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        if sys.platform == "win32":
            signal.signal(signal.SIGTERM, signal_handler)
    
    def cleanup(self):
        """Clean up processes"""
        if self.backend_process and self.backend_process.poll() is None:
            print("  Stopping Backend API...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
        
        if self.frontend_process and self.frontend_process.poll() is None:
            print("  Stopping Streamlit Frontend...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
        
        print("✅ Services stopped gracefully")
    
    def run(self):
        """Run startup sequence"""
        self.print_banner()
        
        if not self.check_environment():
            return False
        
        # Setup signal handlers for Ctrl+C
        self.setup_signal_handlers()
        
        # Start backend
        if not self.start_backend():
            self.print_startup_failed()
            return False
        
        # Wait a bit for backend to stabilize
        time.sleep(2)
        
        # Start frontend
        if not self.start_frontend():
            self.cleanup()
            self.print_startup_failed()
            return False
        
        # All started successfully
        self.print_startup_success()
        
        # Keep processes running
        try:
            while True:
                time.sleep(1)
                
                # Check if processes are still running
                if self.backend_process.poll() is not None:
                    print("⚠️  Backend API crashed!")
                    break
                
                if self.frontend_process.poll() is not None:
                    print("⚠️  Frontend crashed!")
                    break
        
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
        
        return True


def main():
    """Main entry point"""
    manager = StartupManager()
    success = manager.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
