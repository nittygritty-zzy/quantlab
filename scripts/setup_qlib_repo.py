#!/usr/bin/env python3
"""
Setup Qlib Repository Script

This script clones the Microsoft Qlib repository and sets it up for QuantLab.
The qlib_repo directory is excluded from git to keep the repository size small.

Usage:
    uv run python scripts/setup_qlib_repo.py

    # Or with specific branch/tag
    uv run python scripts/setup_qlib_repo.py --branch v0.9.1

    # Force re-clone
    uv run python scripts/setup_qlib_repo.py --force
"""

import argparse
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(message: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.GREEN}✓{Colors.END} {message}")


def print_warning(message: str):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.END}  {message}")


def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.RED}✗{Colors.END} {message}")


def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.BLUE}ℹ{Colors.END}  {message}")


def run_command(cmd: list[str], cwd: Path = None, check: bool = True) -> tuple[int, str, str]:
    """
    Run a shell command and return the result

    Args:
        cmd: Command to run as list
        cwd: Working directory
        check: Raise exception on error

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )

    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            result.stdout,
            result.stderr
        )

    return result.returncode, result.stdout, result.stderr


def check_git_installed() -> bool:
    """Check if git is installed"""
    try:
        run_command(['git', '--version'])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def clone_qlib_repo(
    repo_path: Path,
    branch: str = None,
    force: bool = False
) -> bool:
    """
    Clone the Microsoft Qlib repository

    Args:
        repo_path: Path where to clone the repository
        branch: Specific branch or tag to checkout
        force: Force re-clone if directory exists

    Returns:
        True if successful, False otherwise
    """
    print_header("Cloning Microsoft Qlib Repository")

    # Check if git is installed
    if not check_git_installed():
        print_error("Git is not installed. Please install git first.")
        print_info("macOS: brew install git")
        print_info("Linux: apt-get install git or yum install git")
        return False

    # Check if directory already exists
    if repo_path.exists():
        if not force:
            print_warning(f"Directory {repo_path} already exists.")
            print_info("Use --force to re-clone the repository.")

            # Check if it's a valid git repo
            if (repo_path / '.git').exists():
                print_success("Qlib repository already set up!")
                return True
            else:
                print_error("Directory exists but is not a git repository.")
                print_info("Please remove it manually or use --force.")
                return False
        else:
            print_warning(f"Removing existing directory: {repo_path}")
            import shutil
            shutil.rmtree(repo_path)

    # Clone the repository
    print_info("Cloning from: https://github.com/microsoft/qlib.git")
    if branch:
        print_info(f"Branch/Tag: {branch}")
    else:
        print_info("Branch: main (latest)")

    try:
        # Clone command
        clone_cmd = [
            'git', 'clone',
            'https://github.com/microsoft/qlib.git',
            str(repo_path)
        ]

        print_info("Running: " + " ".join(clone_cmd))
        print_info("This may take 2-5 minutes...")

        returncode, stdout, stderr = run_command(clone_cmd, check=True)

        print_success(f"Repository cloned successfully to: {repo_path}")

        # Checkout specific branch if requested
        if branch:
            print_info(f"Checking out branch/tag: {branch}")
            run_command(['git', 'checkout', branch], cwd=repo_path, check=True)
            print_success(f"Checked out: {branch}")

        # Show repository info
        returncode, stdout, stderr = run_command(
            ['git', 'log', '-1', '--oneline'],
            cwd=repo_path
        )
        print_info(f"Latest commit: {stdout.strip()}")

        return True

    except subprocess.CalledProcessError as e:
        print_error("Failed to clone repository")
        print_error(f"Error: {e.stderr}")
        return False


def apply_patches(repo_path: Path) -> bool:
    """
    Apply custom patches to Qlib

    Args:
        repo_path: Path to the qlib repository

    Returns:
        True if successful, False otherwise
    """
    print_header("Applying Custom Patches")

    # Find patches directory
    project_root = Path(__file__).parent.parent
    patches_dir = project_root / 'patches'

    if not patches_dir.exists():
        print_warning("No patches directory found, skipping patches")
        return True

    # Find all .patch files
    patch_files = sorted(patches_dir.glob('*.patch'))

    if not patch_files:
        print_warning("No patch files found in patches/")
        return True

    print_info(f"Found {len(patch_files)} patch file(s)")

    # Apply each patch
    for patch_file in patch_files:
        print_info(f"Applying {patch_file.name}...")

        try:
            # Try to apply patch
            returncode, stdout, stderr = run_command(
                ['git', 'apply', '--check', str(patch_file)],
                cwd=repo_path,
                check=False
            )

            if returncode != 0:
                print_warning(f"Patch {patch_file.name} check failed, trying anyway...")

            # Apply the patch
            returncode, stdout, stderr = run_command(
                ['git', 'apply', str(patch_file)],
                cwd=repo_path,
                check=False
            )

            if returncode == 0:
                print_success(f"Applied {patch_file.name}")
            else:
                print_error(f"Failed to apply {patch_file.name}")
                print_error(stderr)
                return False

        except Exception as e:
            print_error(f"Error applying {patch_file.name}: {e}")
            return False

    print_success(f"All {len(patch_files)} patches applied successfully!")

    # Show what was modified
    print_info("\nModified files:")
    returncode, stdout, stderr = run_command(
        ['git', 'status', '--short'],
        cwd=repo_path,
        check=False
    )
    if stdout:
        for line in stdout.strip().split('\n'):
            print_info(f"  {line}")

    return True


def install_qlib(repo_path: Path) -> bool:
    """
    Install Qlib in development mode

    Args:
        repo_path: Path to the qlib repository

    Returns:
        True if successful, False otherwise
    """
    print_header("Installing Qlib (Development Mode)")

    if not repo_path.exists():
        print_error(f"Repository not found at: {repo_path}")
        return False

    # Check if setup.py or pyproject.toml exists
    if not (repo_path / 'setup.py').exists() and not (repo_path / 'pyproject.toml').exists():
        print_error("No setup.py or pyproject.toml found in repository")
        return False

    try:
        print_info("Installing Qlib in editable mode...")
        print_info("This may take 2-5 minutes...")

        # Install in editable mode
        returncode, stdout, stderr = run_command(
            ['pip', 'install', '-e', '.'],
            cwd=repo_path,
            check=True
        )

        print_success("Qlib installed successfully!")

        # Verify installation
        print_info("Verifying installation...")
        returncode, stdout, stderr = run_command(
            ['python', '-c', 'import qlib; print(f"Qlib version: {qlib.__version__}")'],
            check=False
        )

        if returncode == 0:
            print_success(stdout.strip())
        else:
            print_warning("Could not verify Qlib version, but installation completed.")

        return True

    except subprocess.CalledProcessError as e:
        print_error("Failed to install Qlib")
        print_error(f"Error: {e.stderr}")
        print_info("\nTry installing manually:")
        print_info(f"  cd {repo_path}")
        print_info("  pip install -e .")
        return False


def verify_setup(repo_path: Path) -> bool:
    """
    Verify the Qlib setup is working

    Args:
        repo_path: Path to the qlib repository

    Returns:
        True if verification passed, False otherwise
    """
    print_header("Verifying Qlib Setup")

    checks = []

    # Check 1: Repository exists
    if repo_path.exists():
        print_success(f"Repository exists: {repo_path}")
        checks.append(True)
    else:
        print_error(f"Repository not found: {repo_path}")
        checks.append(False)

    # Check 2: Git repository
    if (repo_path / '.git').exists():
        print_success("Valid git repository")
        checks.append(True)
    else:
        print_error("Not a valid git repository")
        checks.append(False)

    # Check 3: Qlib importable
    returncode, stdout, stderr = run_command(
        ['python', '-c', 'import qlib'],
        check=False
    )
    if returncode == 0:
        print_success("Qlib can be imported")
        checks.append(True)
    else:
        print_error("Cannot import Qlib")
        print_error(stderr)
        checks.append(False)

    # Check 4: qrun command available
    returncode, stdout, stderr = run_command(
        ['which', 'qrun'],
        check=False
    )
    if returncode == 0:
        print_success(f"qrun command available: {stdout.strip()}")
        checks.append(True)
    else:
        print_warning("qrun command not found in PATH")
        print_info("This is normal if Qlib was just installed. Try restarting your shell.")
        checks.append(True)  # Not critical

    all_passed = all(checks)

    if all_passed:
        print_success("\n✓ All verification checks passed!")
    else:
        print_error("\n✗ Some verification checks failed")

    return all_passed


def show_next_steps(repo_path: Path):
    """Show next steps after setup"""
    print_header("Setup Complete! Next Steps")

    print(f"{Colors.BOLD}1. Verify installation:{Colors.END}")
    print("   python -c 'import qlib; print(qlib.__version__)'")
    print()

    print(f"{Colors.BOLD}2. Initialize Qlib data (if needed):{Colors.END}")
    print("   uv run python scripts/data/setup_quantlab.py")
    print()

    print(f"{Colors.BOLD}3. Pre-compute indicators (optional but recommended):{Colors.END}")
    print("   uv run python scripts/data/precompute_indicators.py")
    print()

    print(f"{Colors.BOLD}4. Run a backtest:{Colors.END}")
    print("   cd qlib_repo")
    print("   uv run qrun ../configs/backtest_dev.yaml")
    print()

    print(f"{Colors.BOLD}5. Repository location:{Colors.END}")
    print(f"   {repo_path.absolute()}")
    print()

    print(f"{Colors.BOLD}Notes:{Colors.END}")
    print(f"   • The qlib_repo/ directory is in .gitignore (not tracked by git)")
    print(f"   • Size: ~828 MB")
    print(f"   • Updates: cd qlib_repo && git pull")
    print()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Clone and setup Microsoft Qlib repository for QuantLab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clone latest version
  python scripts/setup_qlib_repo.py

  # Clone specific version
  python scripts/setup_qlib_repo.py --branch v0.9.1

  # Force re-clone
  python scripts/setup_qlib_repo.py --force

  # Skip installation
  python scripts/setup_qlib_repo.py --no-install
        """
    )

    parser.add_argument(
        '--branch',
        type=str,
        default=None,
        help='Specific branch or tag to checkout (default: main)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-clone even if directory exists'
    )

    parser.add_argument(
        '--no-install',
        action='store_true',
        help='Skip installation step (clone only)'
    )

    parser.add_argument(
        '--repo-path',
        type=Path,
        default=None,
        help='Custom path for qlib repository (default: ./qlib_repo)'
    )

    args = parser.parse_args()

    # Determine repository path
    if args.repo_path:
        repo_path = args.repo_path
    else:
        # Default: qlib_repo in project root
        project_root = Path(__file__).parent.parent
        repo_path = project_root / 'qlib_repo'

    print_header("QuantLab - Qlib Repository Setup")
    print_info(f"Target directory: {repo_path}")

    # Step 1: Clone repository
    success = clone_qlib_repo(repo_path, args.branch, args.force)
    if not success:
        print_error("\nSetup failed at clone step")
        sys.exit(1)

    # Step 2: Apply patches
    success = apply_patches(repo_path)
    if not success:
        print_error("\nSetup failed at patch application step")
        print_info("Check the errors above")
        print_info("Patches are in: patches/")
        sys.exit(1)

    # Step 3: Install Qlib (unless --no-install)
    if not args.no_install:
        success = install_qlib(repo_path)
        if not success:
            print_error("\nSetup failed at installation step")
            print_info("You can try installing manually or run with --no-install")
            sys.exit(1)
    else:
        print_info("Skipping installation (--no-install flag)")

    # Step 4: Verify setup
    success = verify_setup(repo_path)
    if not success:
        print_warning("\nSetup completed but verification failed")
        print_info("Check the errors above and try installing manually")
        sys.exit(1)

    # Step 5: Show next steps
    show_next_steps(repo_path)

    print_success("Setup completed successfully! 🎉")


if __name__ == '__main__':
    main()
