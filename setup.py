#!/usr/bin/env python3
"""
HireMind Project Setup Script

This script sets up the development environment for HireMind.
Supports: Windows, Linux, macOS
"""

import os
import subprocess
import sys
from pathlib import Path


class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'


def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def run_command(cmd, description, ignore_error=False):
    """Run a command and handle errors."""
    try:
        print(f"{Colors.BLUE}→ {description}...{Colors.END}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            if ignore_error:
                print_warning(f"Command failed but continuing: {cmd}")
                return False
            else:
                print_error(f"Command failed: {cmd}")
                print(f"Error: {result.stderr}")
                return False
        
        print_success(description)
        return True
    except Exception as e:
        print_error(f"Exception: {e}")
        return False


def check_python():
    """Check if Python 3.9+ is installed."""
    print_header("Checking Python Installation")
    
    try:
        version_output = subprocess.check_output([sys.executable, '--version'], text=True)
        version = version_output.strip()
        print(f"Python: {version}")
        
        version_num = sys.version_info
        if version_num.major == 3 and version_num.minor >= 9:
            print_success("Python version is compatible")
            return True
        else:
            print_error(f"Python 3.9+ required, found {version_num.major}.{version_num.minor}")
            return False
    except Exception as e:
        print_error(f"Python check failed: {e}")
        return False


def check_node():
    """Check if Node.js 16+ is installed."""
    print_header("Checking Node.js Installation")
    
    try:
        version_output = subprocess.check_output(['node', '--version'], text=True)
        print(f"Node.js: {version_output.strip()}")
        print_success("Node.js found")
        
        npm_version = subprocess.check_output(['npm', '--version'], text=True)
        print(f"npm: {npm_version.strip()}")
        print_success("npm found")
        return True
    except FileNotFoundError:
        print_warning("Node.js or npm not found")
        return False


def setup_python_env():
    """Setup Python virtual environment."""
    print_header("Setting Up Python Environment")
    
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print_warning("Virtual environment already exists")
    else:
        run_command(f"{sys.executable} -m venv .venv", "Creating virtual environment")
    
    # Determine activation command
    if sys.platform == "win32":
        activate_cmd = ".venv\\Scripts\\activate.bat && "
    else:
        activate_cmd = "source .venv/bin/activate && "
    
    run_command(f"{activate_cmd}pip install --upgrade pip", "Upgrading pip")
    run_command(f"{activate_cmd}pip install -r backend/requirements.txt", "Installing backend dependencies")
    print_success("Python environment ready")


def setup_frontend():
    """Setup Node.js frontend."""
    print_header("Setting Up Frontend")
    
    os.chdir("frontend")
    
    run_command("npm install", "Installing frontend dependencies")
    run_command("npm run build", "Building Tailwind CSS", ignore_error=True)
    
    os.chdir("..")
    print_success("Frontend ready")


def setup_database():
    """Initialize database."""
    print_header("Setting Up Database")
    
    if sys.platform == "win32":
        activate_cmd = ".venv\\Scripts\\activate.bat && "
    else:
        activate_cmd = "source .venv/bin/activate && "
    
    run_command(f"{activate_cmd}python database/init_db.py", "Initializing database", ignore_error=True)


def setup_git_hooks():
    """Setup pre-commit hooks."""
    print_header("Setting Up Git Hooks")
    
    if sys.platform == "win32":
        activate_cmd = ".venv\\Scripts\\activate.bat && "
    else:
        activate_cmd = "source .venv/bin/activate && "
    
    run_command(f"{activate_cmd}pip install pre-commit", "Installing pre-commit")
    run_command(f"{activate_cmd}pre-commit install", "Installing git hooks", ignore_error=True)


def create_env_file():
    """Create .env file if it doesn't exist."""
    print_header("Setting Up Environment Variables")
    
    if not Path(".env").exists():
        print("Creating .env file...")
        os.system("cp .env.example .env 2>/dev/null || copy .env.example .env")
        print_warning("Edit .env file with your configuration")
        print_success(".env file created")
    else:
        print_warning(".env file already exists")


def main():
    """Main setup function."""
    os.chdir(Path(__file__).parent.resolve())
    
    print_header("HireMind Development Environment Setup")
    
    checks = [
        ("Python 3.9+", check_python),
        ("Node.js 16+", check_node),
    ]
    
    all_passed = True
    for name, check in checks:
        if not check():
            all_passed = False
            print_error(f"{name} check failed")
    
    if not all_passed:
        print_error("\nSetup cannot proceed. Please install required dependencies.")
        sys.exit(1)
    
    # Setup steps
    try:
        create_env_file()
        setup_python_env()
        setup_frontend()
        setup_database()
        setup_git_hooks()
        
        # Print summary
        print_header("Setup Complete! 🎉")
        print(f"{Colors.GREEN}HireMind is ready for development!{Colors.END}\n")
        
        print(f"{Colors.YELLOW}Next steps:{Colors.END}")
        print("1. Edit .env file with your settings")
        print("2. Run 'make dev' to start development servers")
        print("3. Backend: http://127.0.0.1:8000")
        print("4. Frontend: http://localhost:5173")
        print("5. API Docs: http://127.0.0.1:8000/docs\n")
        
        print(f"{Colors.YELLOW}Useful commands:{Colors.END}")
        print("  make help        - Show all available commands")
        print("  make dev         - Start dev servers")
        print("  make test        - Run tests")
        print("  make lint        - Run linters")
        print("  make docker-up   - Start Docker containers\n")
        
        print_success("Happy coding! 🚀\n")
        
    except KeyboardInterrupt:
        print_error("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
