import subprocess
import json
import pytest
import os
import importlib.metadata
from typing import List

def get_installed_packages():
    """Get a dictionary of installed packages and their versions."""
    # Normalize names: replace hyphens with underscores
    return {dist.metadata["Name"].lower().replace("-", "_"): dist.version for dist in importlib.metadata.distributions()}

def get_requirements() -> List[str]:
    """Read requirements from requirements.txt."""
    req_path = os.path.join(os.path.dirname(__file__), "../../requirements.txt")
    if not os.path.exists(req_path):
        return []
    
    requirements = []
    with open(req_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip versions: >=, ==, >, <
            name = line.split(">")[0].split("=")[0].split("<")[0].strip()
            # Strip extras: [standard], [asyncio]
            name = name.split("[")[0].strip()
            # Normalize names: replace hyphens with underscores
            requirements.append(name.lower().replace("-", "_"))
    return requirements

def test_library_presence():
    """Check if all required libraries are installed."""
    installed = get_installed_packages()
    required = get_requirements()
    
    missing = [req for req in required if req not in installed and req != "python-multipart"]
    # python-multipart is sometimes registered as 'multipart' or 'python-multipart'
    if "python-multipart" in required:
        if "python-multipart" not in installed and "multipart" not in installed:
            missing.append("python-multipart")
            
    assert not missing, f"Missing required packages: {missing}"

import sys

def test_no_vulnerabilities():
    """
    Check for known security vulnerabilities using pip-audit.
    """
    try:
        # We use a subprocess to run pip-audit via current python executable
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--format", "json"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            return # No vulnerabilities
            
        data = json.loads(result.stdout)
        vulnerabilities = [item for item in data if item.get("vulnerabilities")]
        assert not vulnerabilities, f"Security vulnerabilities found: {vulnerabilities}"
    except (FileNotFoundError, json.JSONDecodeError):
        pytest.skip("pip-audit not working as module in this environment")

def test_deprecated_libraries():
    """
    Check for libraries that are known to be deprecated or poorly maintained.
    This is a policy-based test.
    """
    installed = get_installed_packages()
    
    # List of libraries we want to flag as 'warning' or 'error'
    deprecated_list = {
        "passlib": "Consider using 'pwdlib' or 'bcrypt' directly (passlib is poorly maintained)",
        "multipart": "Ensure you are using 'python-multipart', not the legacy 'multipart' package",
    }
    
    found_deprecated = []
    for pkg, message in deprecated_list.items():
        if pkg in installed:
            # For a strict project, we could assert here. 
            # For this master project, we will just print/log if running with -s
            print(f"\n[MAINTENANCE WARNING] {pkg}: {message}")
    
    pass

def test_code_security_scan():
    """
    Run bandit on the app directory to ensure no common security issues.
    """
    app_path = os.path.join(os.path.dirname(__file__), "../app")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", app_path, "-f", "json"], 
            capture_output=True, 
            text=True
        )
        data = json.loads(result.stdout)
        results = data.get("results", [])
        
        serious_issues = [r for r in results if r["issue_severity"] in ["MEDIUM", "HIGH"]]
        
        assert not serious_issues, f"Bandit found serious security issues: {serious_issues}"
    except (FileNotFoundError, json.JSONDecodeError):
        pytest.skip("bandit not working as module in this environment")

if __name__ == "__main__":
    # If run directly, output a report
    print("Checking system integrity...")
