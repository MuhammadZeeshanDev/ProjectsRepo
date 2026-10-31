"""Run once from a terminal: create the first SQL Server administrator."""
import getpass
from quantumsafe import db, users


def main():
    if not db.database_ready():
        raise SystemExit("Cannot reach SQL Server. Check the .env and SQL script.")
    if db.one("SELECT TOP 1 UserId FROM dbo.Users"):
        raise SystemExit("Users already exist. Ask an Admin to add more users.")
    name = input("Choose admin username: ").strip()
    first = getpass.getpass("Choose admin password (12+ characters): ")
    again = getpass.getpass("Repeat password: ")
    if first != again:
        raise SystemExit("Passwords do not match; no account created.")
    users.create_user(None, name, first, "Admin", initial_admin=True)
    print("Admin account created. Run the Streamlit application to sign in.")


if __name__ == "__main__":
    main()
