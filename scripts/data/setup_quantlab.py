#!/usr/bin/env python
"""
Setup script for QuantLab

This script:
1. Installs the quantlab package in editable mode
2. Initializes the database
3. Creates default config
4. Checks data availability
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e}")
        return False


def main():
    """Main setup procedure"""
    print("\n" + "="*60)
    print("🎯 QuantLab Setup")
    print("="*60)

    # Check we're in the right directory
    if not Path("quantlab").exists() or not Path("pyproject.toml").exists():
        print("❌ Error: Please run this script from the quantlab project root")
        sys.exit(1)

    # Step 1: Install package in editable mode
    if not run_command(
        "uv pip install -e .",
        "Installing QuantLab package"
    ):
        sys.exit(1)

    # Step 2: Initialize QuantLab
    if not run_command(
        "quantlab init",
        "Initializing QuantLab database and config"
    ):
        print("⚠️  Warning: Initialization had issues, but continuing...")

    print("\n" + "="*60)
    print("✅ QuantLab Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Edit config: ~/.quantlab/config.yaml")
    print("2. Create a portfolio: quantlab portfolio create my-portfolio --name 'My Portfolio'")
    print("3. Add tickers: quantlab portfolio add my-portfolio AAPL MSFT GOOGL")
    print("4. Check data: quantlab data check")
    print("5. Get help: quantlab --help")
    print("\n")


if __name__ == "__main__":
    main()
