import getpass
import sqlite3
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

ALLOWED_ROLES = {"staff", "recipient", "management"}


def main():
    from app import create_app
    from app.db import get_db

    username = input("Enter username: ").strip()

    if not username:
        print("Error: Username cannot be empty.")
        return 1

    print("Available roles: staff, recipient, management")
    role = input("Enter role: ").strip().lower()

    if role not in ALLOWED_ROLES:
        print("Error: Invalid role.")
        return 1

    password = getpass.getpass("Enter password (minimum 12 characters): ")
    confirm_password = getpass.getpass("Confirm password: ")

    if len(password) < 12:
        print("Error: Password must contain at least 12 characters.")
        return 1

    if password != confirm_password:
        print("Error: Passwords do not match.")
        return 1

    app = create_app()

    with app.app_context():
        db = get_db()

        try:
            db.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
                """,
                (
                    username,
                    generate_password_hash(password),
                    role,
                ),
            )
            db.commit()

        except sqlite3.IntegrityError:
            print("Error: That username already exists.")
            return 1

        except sqlite3.Error:
            print("Error: Unable to create the user account.")
            return 1

    print(f"User '{username}' created successfully with role '{role}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())