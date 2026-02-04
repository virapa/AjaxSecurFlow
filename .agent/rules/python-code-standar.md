---
trigger: always_on
---

# 🚀 Antigravity Project - Global Rules & Style Guide

This document establishes the "golden rules" for development within this project. All scripts and modules must adhere to these standards to ensure consistency and scalability.

---

## 🌍 1. Language Standard
* **English Only:** All code (variable names, functions, classes, comments, and log messages) must be written exclusively in **English**.
    * *Correct:* `calculate_velocity()`
    * *Incorrect:* `calcular_velocidad()`

---

## 🐍 2. Naming Conventions (PEP 8)
To maintain harmony with the Python ecosystem, the following formats shall be used:

| Element | Style | Example |
| :--- | :--- | :--- |
| **Variables** | `snake_case` | `current_altitude` |
| **Functions** | `snake_case` | `deploy_parachute()` |
| **Classes** | `PascalCase` | `FlightController` |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_GRAVITY_THRESHOLD` |
| **Modules/Files** | `snake_case` | `gravity_utils.py` |

---

## 🔑 3. Environment Variables & Configuration
Sensitive values (API keys, credentials, local paths) must never be hardcoded.

* **Mandatory Usage:** A `.env` file must be used for local configuration.
* **Data Loading:** Code should load environment variables at startup using `python-dotenv` or the `os` module.
* **Prefix:** Global project environment variables should start with the `ANTIGRAVITY_` prefix.
    * *Example:* `ANTIGRAVITY_API_KEY=secret_value`

---

## 📁 4. Diagnostic Files
* **Naming Convention:** Any Python file created for diagnostic or testing purposes must start with the `diag_` prefix.
* **Git Policy:** These files are strictly local and must never be committed to the repository.
    * *Example:* `diag_connection_test.py`

---

## 🛠️ 5. Project Initialization Pattern
Every main script should follow this minimum structure to ensure environment variables are available:

```python
import os
from dotenv import load_dotenv

# Initialize environment variables
load_dotenv()

def main_process():
    # Use snake_case for local variables
    api_key = os.getenv("ANTIGRAVITY_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTIGRAVITY_API_KEY is not set.")
    print("System ready to fly.")

if __name__ == "__main__":
    main_process()