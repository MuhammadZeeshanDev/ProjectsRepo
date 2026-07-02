package service;

import db.DatabaseManager;

import java.sql.*;
import java.util.UUID;

public class AppointmentService {

    public static boolean bookAppointment(String name, int age, String gender, String date, String dept) {
        try (Connection conn = DatabaseManager.getConnection()) {
            String sql = "INSERT INTO appointments (id, name, age, gender, date, department) VALUES (?, ?, ?, ?, ?, ?)";
            PreparedStatement stmt = conn.prepareStatement(sql);
            stmt.setString(1, UUID.randomUUID().toString());
            stmt.setString(2, name);
            stmt.setInt(3, age);
            stmt.setString(4, gender);
            stmt.setString(5, date);
            stmt.setString(6, dept);
            return stmt.executeUpdate() > 0;
        } catch (SQLException e) {
            e.printStackTrace();
            return false;
        }
    }
}
