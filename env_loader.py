# ============================================================
# ENV LOADER MODULE
# Simple .env file parser for MicroPython
# ============================================================

def load_env(filename='.env'):
    """Load environment variables from .env file
    Returns dictionary of key-value pairs
    """
    env = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
    except FileNotFoundError:
        print("Warning: .env file not found")
    except Exception as e:
        print("Error loading .env:", e)
    return env
