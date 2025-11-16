#!/usr/bin/env python3
"""
DocZilla Test Runner Script

Runs the test suite with proper configuration.
"""

import sys
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


def check_pytest():
    """Check if pytest is installed."""
    try:
        import pytest
        return True
    except ImportError:
        return False


def run_tests(test_type: str = "all", coverage: bool = True):
    """Run tests."""
    project_root = Path(__file__).parent.parent
    
    # Check pytest
    if not check_pytest():
        print_error("pytest not found")
        print("Install with: pip install pytest pytest-cov")
        sys.exit(1)
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
    elif test_type == "e2e":
        cmd.append("tests/e2e_smoke/")
    else:
        cmd.append("tests/")
    
    if coverage:
        cmd.extend([
            "--cov=src/app",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=80"
        ])
    
    cmd.extend(["-v"])
    
    print_header(f"Running {test_type} Tests")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=False)
        if result.returncode == 0:
            print_success("All tests passed!")
            if coverage:
                print(f"\nCoverage report: {project_root / 'htmlcov' / 'index.html'}")
        else:
            print_error("Some tests failed")
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to run tests: {e}")
        sys.exit(1)


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run DocZilla test suite")
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "e2e"],
        default="all",
        help="Test type to run"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting"
    )
    
    args = parser.parse_args()
    
    exit_code = run_tests(
        test_type=args.type,
        coverage=not args.no_coverage
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

