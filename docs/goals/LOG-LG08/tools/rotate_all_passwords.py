
import os
import sys
from core.auth import hash_password
from core.database import update_user, load_users

def rotate():
    # New passwords from environment variables to avoid plaintext in code
    passwords = {
        "admin": os.environ.get("NEW_PASS_ADMIN"),
        "7roger": os.environ.get("NEW_PASS_7ROGER"),
        "sami": os.environ.get("NEW_PASS_SAMI"),
        "fiona": os.environ.get("NEW_PASS_FIONA"),
    }
    
    missing = [u for u, p in passwords.items() if not p]
    if missing:
        print(f"FAIL: Missing env vars for: {missing}")
        return False
        
    current_users = load_users()
    for username, new_pass in passwords.items():
        if username not in current_users:
            print(f"SKIP: User {username} not found in DB.")
            continue
            
        new_hash = hash_password(new_pass)
        success = update_user(username, {"password_hash": new_hash}, actor="system_rotation")
        if success:
            print(f"OK: Rotated password for {username}")
        else:
            print(f"FAIL: Could not update {username}")
            return False
            
    return True

if __name__ == "__main__":
    if rotate():
        print("SUCCESS: All production passwords rotated.")
        sys.exit(0)
    else:
        sys.exit(1)
