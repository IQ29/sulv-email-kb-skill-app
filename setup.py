#!/usr/bin/env python3
"""
Setup script for SULV Unified Knowledge Base.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path
import shutil


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)


def run_command(cmd, cwd=None):
    """Run a shell command and print output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    if result.stdout:
        print(result.stdout)
    
    return True


def main():
    """Main setup function."""
    print_header("SULV Unified Knowledge Base Setup")
    
    project_dir = Path(__file__).parent
    print(f"Project directory: {project_dir}")
    
    # Step 1: Create virtual environment
    print_header("Step 1: Creating virtual environment")
    venv_path = project_dir / "venv"
    
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        response = input("Recreate? (y/N): ").strip().lower()
        if response == 'y':
            shutil.rmtree(venv_path)
            print("Removed existing virtual environment")
        else:
            print("Using existing virtual environment")
    
    if not venv_path.exists():
        print(f"Creating virtual environment at {venv_path}")
        venv.create(venv_path, with_pip=True)
        print("Virtual environment created")
    
    # Determine Python executable
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    print(f"Python: {python_exe}")
    print(f"Pip: {pip_exe}")
    
    # Step 2: Install dependencies
    print_header("Step 2: Installing dependencies")
    requirements_file = project_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"Error: requirements.txt not found at {requirements_file}")
        return False
    
    if not run_command(f'"{pip_exe}" install -r "{requirements_file}"'):
        print("Failed to install dependencies")
        return False
    
    # Step 3: Initialize database
    print_header("Step 3: Initializing database")
    init_script = project_dir / "scripts" / "init_db.py"
    
    if not init_script.exists():
        print(f"Error: init_db.py not found at {init_script}")
        return False
    
    if not run_command(f'"{python_exe}" "{init_script}"'):
        print("Failed to initialize database")
        return False
    
    # Step 4: Create environment file template
    print_header("Step 4: Creating environment configuration")
    env_template = project_dir / ".env.template"
    env_file = project_dir / ".env"
    
    if not env_file.exists():
        print(f"Creating .env file from template")
        shutil.copy(env_template, env_file)
        print(f"Created {env_file}")
        print("Please edit this file to add your API keys and configuration")
    else:
        print(f".env file already exists at {env_file}")
    
    # Step 5: Create logs directory
    print_header("Step 5: Creating directories")
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    print(f"Created logs directory: {logs_dir}")
    
    # Step 6: Test installation
    print_header("Step 6: Testing installation")
    test_cmd = f'"{python_exe}" -c "import fastapi; import sqlalchemy; print(\'✅ Core dependencies installed\')"'
    if not run_command(test_cmd):
        print("Installation test failed")
        return False
    
    # Summary
    print_header("Setup Complete!")
    print("\nNext steps:")
    print(f"1. Edit configuration: {project_dir / '.env'}")
    print(f"2. Start the API server: {python_exe} src/core/api/server.py")
    print(f"3. Test the API: {python_exe} scripts/test_api.py")
    print(f"4. Check the database: sqlite3 data/kb.db '.tables'")
    print("\nFor development:")
    print(f"  Activate virtual environment:")
    if sys.platform == "win32":
        print(f"    {venv_path / 'Scripts' / 'activate'}")
    else:
        print(f"    source {venv_path / 'bin' / 'activate'}")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nSetup failed with error: {e}")
        sys.exit(1)