#!/usr/bin/env python3
"""
DocZilla Setup Script

This script sets up the DocZilla application environment:
- Verifies Windows compatibility
- Lists available Python versions
- Creates virtual environment
- Installs dependencies
- Creates necessary directories
"""

import sys
import platform
import subprocess
import json
from pathlib import Path
import argparse

# Color codes for Windows terminal
try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    # Fallback if colorama not installed
    class Fore:
        GREEN = ""
        YELLOW = ""
        RED = ""
        CYAN = ""
        RESET = ""
    class Style:
        BRIGHT = ""
        RESET_ALL = ""


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"{text:^60}")
    print(f"{'='*60}{Style.RESET_ALL}{Fore.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Fore.GREEN}✓ {text}{Fore.RESET}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Fore.YELLOW}⚠ {text}{Fore.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Fore.RED}✗ {text}{Fore.RESET}")


def check_windows():
    """Verify Windows compatibility."""
    print_header("Checking System Compatibility")
    
    system = platform.system()
    if system != "Windows":
        print_warning(f"System detected: {system}")
        print_warning("DocZilla is tested on Windows 10/11")
        print_warning("It may work on other systems but is not officially supported")
        # Non-interactive safe default: continue
    else:
        print_success(f"Windows detected: {platform.version()}")
    
    return True


def list_python_versions():
    """List available Python versions using py launcher."""
    print_header("Detecting Python Versions")
    
    try:
        # Use py -0p to list installed Python versions
        result = subprocess.run(
            ["py", "-0p"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0 and result.stdout.strip():
            versions = []
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip() and not line.startswith('-'):
                    # Parse version from py -0p output
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        version = parts[0]
                        path = ' '.join(parts[1:])
                        versions.append((version, path))
            
            if versions:
                print("Available Python versions:")
                for i, (version, path) in enumerate(versions, 1):
                    print(f"  {i}. Python {version} - {path}")
                return versions
            else:
                print_warning("Could not parse Python versions")
        else:
            print_warning("py launcher not found or no output")
    
    except FileNotFoundError:
        print_warning("Python launcher (py) not found")
    
    # Fallback: try python command
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        path = sys.executable
        print_success(f"Using current Python: {version} - {path}")
        return [(version.split()[1], path)]
    except Exception as e:
        print_error(f"Could not detect Python: {e}")
        sys.exit(1)


def select_python_version(versions):
    """Let user select Python version."""
    if len(versions) == 1:
        return versions[0]
    
    print_header("Select Python Version")
    while True:
        try:
            choice = input(f"Enter version number (1-{len(versions)}): ")
            index = int(choice) - 1
            if 0 <= index < len(versions):
                return versions[index]
            else:
                print_error("Invalid selection")
        except ValueError:
            print_error("Please enter a number")
        except KeyboardInterrupt:
            print("\nSetup cancelled.")
            sys.exit(0)


def create_venv(python_path, venv_path):
    """Create virtual environment."""
    print_header("Creating Virtual Environment")
    
    venv_path = Path(venv_path)
    if venv_path.exists():
        print_warning(f"Virtual environment already exists: {venv_path}")
        # Non-interactive: reuse existing env
        return str(venv_path / "Scripts" / "python.exe")
    
    try:
        # Create venv
        subprocess.run(
            [python_path, "-m", "venv", str(venv_path)],
            check=True
        )
        print_success(f"Virtual environment created: {venv_path}")
        
        # Return path to venv Python
        if platform.system() == "Windows":
            venv_python = venv_path / "Scripts" / "python.exe"
        else:
            venv_python = venv_path / "bin" / "python"
        
        return str(venv_python)
    
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        sys.exit(1)


def install_dependencies(venv_python, include_dev=False):
    """Install dependencies."""
    print_header("Installing Dependencies")
    
    project_root = Path(__file__).parent.parent
    req_file = project_root / "requirements" / "base.txt"
    dev_req_file = project_root / "requirements" / "dev.txt"
    
    if not req_file.exists():
        print_error(f"Requirements file not found: {req_file}")
        sys.exit(1)
    
    # Upgrade pip first
    print("Upgrading pip...")
    subprocess.run(
        [venv_python, "-m", "pip", "install", "--upgrade", "pip"],
        check=True
    )
    print_success("pip upgraded")
    
    # Install base requirements
    print(f"\nInstalling base requirements from {req_file.name}...")
    subprocess.run(
        [venv_python, "-m", "pip", "install", "-r", str(req_file)],
        check=True
    )
    print_success("Base requirements installed")
    
    # Install dev requirements if requested
    if include_dev and dev_req_file.exists():
        print(f"\nInstalling dev requirements from {dev_req_file.name}...")
        subprocess.run(
            [venv_python, "-m", "pip", "install", "-r", str(dev_req_file)],
            check=True
        )
        print_success("Dev requirements installed")


def create_directories():
    """Create necessary directories."""
    print_header("Creating Directories")
    
    project_root = Path(__file__).parent.parent
    directories = ["logs", "temp", "src/app/config"]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print_success(f"Created: {dir_path}")


def save_config(venv_path):
    """Save configuration with venv path."""
    project_root = Path(__file__).parent.parent
    config_file = project_root / ".doczilla_config.json"
    
    config = {
        "venv_path": str(venv_path),
        "created": platform.node(),
        "python_version": platform.python_version()
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print_success("Configuration saved")


def parse_args():
    parser = argparse.ArgumentParser(description="DocZilla setup")
    parser.add_argument("--install", choices=["app", "dev"], default="app", help="Install type: app (default) or dev (includes tests and tools)")
    parser.add_argument("--non-interactive", action="store_true", help="Run without prompts using defaults")
    parser.add_argument("--python-path", type=str, default=None, help="Path to python executable to create venv")
    return parser.parse_args()


def main():
    """Main setup function."""
    args = parse_args()
    print_header("DocZilla Setup")
    
    # Check Windows
    check_windows()
    
    # Determine Python path
    if args.python_path:
        python_path = args.python_path
        selected_version = "custom"
        print_success(f"Using provided Python: {python_path}")
    else:
        versions = list_python_versions()
        if not versions:
            print_error("No Python versions found")
            sys.exit(1)
        if args.non_interactive:
            selected_version, python_path = versions[0]
            print_success(f"Auto-selected: Python {selected_version}")
        else:
            selected_version, python_path = select_python_version(versions)
            print_success(f"Selected: Python {selected_version}")
    
    # Create venv
    project_root = Path(__file__).parent.parent
    venv_path = project_root / ".venv_doczilla"
    venv_python = create_venv(python_path, venv_path)
    
    # Install dependencies
    include_dev = (args.install == "dev")
    install_dependencies(venv_python, include_dev=include_dev)
    
    # Create directories
    create_directories()
    
    # Save config
    save_config(venv_path)
    
    # Final message
    print_header("Setup Complete!")
    print_success("Virtual environment created and dependencies installed")
    print(f"\nTo run the app, execute:")
    print(f"  {Fore.CYAN}python scripts/run_app.py{Fore.RESET}")
    print(f"\nOr manually:")
    print(f"  {Fore.CYAN}.venv_doczilla\\Scripts\\activate{Fore.RESET}")
    print(f"  {Fore.CYAN}streamlit run src/app/main.py{Fore.RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

