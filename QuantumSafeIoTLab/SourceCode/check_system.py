"""Small beginner-friendly preflight check. No private data is printed."""
from quantumsafe import db, crypto_engine


def main():
    print("[1] SQL Server connection:", "OK" if db.database_ready() else "NOT CONNECTED")
    print("[2] Real ML-KEM self-tests:")
    for name in crypto_engine.ALGORITHMS:
        try:
            answer = crypto_engine.self_test(name)
            print("  ", name, "PASS", answer["sizes"])
        except Exception as exc:
            print("  ", name, "NOT READY:", type(exc).__name__, str(exc))


if __name__ == "__main__":
    main()
