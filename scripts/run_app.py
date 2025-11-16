#!/usr/bin/env python3
"""
DocZilla Run Script

This script runs the DocZilla application:
- Checks for virtual environment
- Verifies dependencies
- Launches Streamlit app
"""

import sys
import json
import subprocess
from pathlib import Path

# Color codes for Windows terminal
try:
    from colorama import init, Fore, Style
    init()
except ImportError:
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


def print_error(text: str):
    """Print error message."""
    print(f"{Fore.RED}✗ {text}{Fore.RESET}")


def check_venv():
    """Check if virtual environment exists."""
    project_root = Path(__file__).parent.parent
    venv_path = project_root / ".venv_doczilla"
    
    if not venv_path.exists():
        print_error("Virtual environment not found")
        print(f"Run {Fore.CYAN}python scripts/setup_app.py{Fore.RESET} first")
        sys.exit(1)
    
    # Get Python executable
    import platform
    if platform.system() == "Windows":
        python_exe = venv_path / "Scripts" / "python.exe"
        streamlit_exe = venv_path / "Scripts" / "streamlit.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        streamlit_exe = venv_path / "bin" / "streamlit"
    
    if not python_exe.exists():
        print_error(f"Python executable not found: {python_exe}")
        sys.exit(1)
    
    return str(python_exe), str(streamlit_exe)


def check_dependencies(python_exe):
    """Check if core dependencies are installed."""
    print_header("Checking Dependencies")
    
    core_dependencies = [
        "streamlit",
        "pandas",
        "numpy",
        "Pillow"
    ]
    
    missing = []
    for dep in core_dependencies:
        try:
            result = subprocess.run(
                [python_exe, "-m", "pip", "show", dep],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                print_success(f"{dep} installed")
            else:
                print_error(f"{dep} not found")
                missing.append(dep)
        except Exception as e:
            print_error(f"Error checking {dep}: {e}")
            missing.append(dep)
    
    if missing:
        print_error(f"Missing dependencies: {', '.join(missing)}")
        print(f"Run {Fore.CYAN}python scripts/setup_app.py{Fore.RESET} to install")
        sys.exit(1)
    
    return True


def check_app_files():
    """Check if app files exist."""
    project_root = Path(__file__).parent.parent
    main_file = project_root / "src" / "app" / "main.py"
    
    if not main_file.exists():
        print_error(f"Main app file not found: {main_file}")
        sys.exit(1)
    
    return True


def run_app(streamlit_exe, python_exe):
    """Run the Streamlit app."""
    project_root = Path(__file__).parent.parent
    main_file = project_root / "src" / "app" / "main.py"
    
    print_header("Starting DocZilla")
    print_success("Launching Streamlit...")
    print(f"\nApp will open in your browser automatically")
    print(f"Press Ctrl+C to stop the app\n")
    
    try:
        # Set PYTHONPATH to include project root for proper imports
        import os
        env = os.environ.copy()
        current_pythonpath = env.get("PYTHONPATH", "")
        if current_pythonpath:
            env["PYTHONPATH"] = f"{str(project_root)}{os.pathsep}{current_pythonpath}"
        else:
            env["PYTHONPATH"] = str(project_root)
        
        # Run streamlit
        subprocess.run(
            [streamlit_exe, "run", str(main_file)],
            check=True,
            env=env
        )
    except KeyboardInterrupt:
        print("\n\nApp stopped by user.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start app: {e}")
        sys.exit(1)


def main():
    """Main run function."""
    print_header("DocZilla Launcher")
    
    # Check venv
    python_exe, streamlit_exe = check_venv()
    print_success("Virtual environment found")
    
    # Check dependencies
    check_dependencies(python_exe)
    
    # Check app files
    check_app_files()
    print_success("App files verified")
    
    # Run app
    run_app(streamlit_exe, python_exe)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nLaunch cancelled.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Launch failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

