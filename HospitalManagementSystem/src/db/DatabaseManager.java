package db;

import java.sql.*;

public class DatabaseManager {
    private static final String URL = "jdbc:sqlite:hospital.db";
    private static Connection conn = null;

    static {
        try {
            Class.forName("org.sqlite.JDBC"); // Load driver
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
    }

    public static Connection getConnection() {
        try {
            if (conn == null || conn.isClosed()) {
                conn = DriverManager.getConnection(URL);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return conn;
    }

    public static void initialize() {
        try (Connection conn = DriverManager.getConnection(URL); Statement stmt = conn.createStatement()) {
            // Create all your tables
            stmt.execute("""
                CREATE TABLE IF NOT EXISTS admin (
                    username TEXT PRIMARY KEY,
                    password TEXT
                )
            """);

            stmt.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    age INTEGER,
                    gender TEXT,
                    ward TEXT,
                    status TEXT,
                    date TEXT
                )
            """);

            stmt.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    age INTEGER,
                    gender TEXT,
                    date TEXT,
                    department TEXT
                )
            """);

            stmt.execute("""
                CREATE TABLE IF NOT EXISTS blood_bank (
                    type TEXT PRIMARY KEY,
                    units INTEGER
                )
            """);

            stmt.execute("""
                CREATE TABLE IF NOT EXISTS pharmacy (
                    item TEXT PRIMARY KEY,
                    quantity INTEGER
                )
            """);

            stmt.execute("""
                CREATE TABLE IF NOT EXISTS wards (
                    name TEXT PRIMARY KEY,
                    total_beds INTEGER,
                    occupied_beds INTEGER
                )
            """);

            stmt.execute("""
                CREATE TABLE IF NOT EXISTS deceased (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    date TEXT,
                    reason TEXT
                )
            """);

            stmt.execute("""
    CREATE TABLE IF NOT EXISTS opd (
        id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        symptoms TEXT
    );
""");

            stmt.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        date TEXT,
        department TEXT
    );
""");


            // Default admin account
            stmt.execute("INSERT OR IGNORE INTO admin (username, password) VALUES ('admin', 'admin123')");

        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
}
