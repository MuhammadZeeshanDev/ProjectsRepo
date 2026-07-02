package service;

import db.DatabaseManager;

import java.sql.*;
import java.util.HashMap;
import java.util.Map;

public class WardService {

    public static Map<String, int[]> getAllWards() {
        Map<String, int[]> wardData = new HashMap<>();

        String sql = "SELECT * FROM wards";
        try (Connection conn = DatabaseManager.getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            while (rs.next()) {
                String name = rs.getString("name");
                int total = rs.getInt("total_beds");
                int occupied = rs.getInt("occupied_beds");
                wardData.put(name, new int[]{total, occupied});
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }

        return wardData;
    }

    public static void addOrUpdateWard(String name, int totalBeds) {
        String checkSql = "SELECT * FROM wards WHERE name = ?";
        String insertSql = "INSERT INTO wards (name, total_beds, occupied_beds) VALUES (?, ?, 0)";
        String updateSql = "UPDATE wards SET total_beds = ? WHERE name = ?";

        try (Connection conn = DatabaseManager.getConnection();
             PreparedStatement check = conn.prepareStatement(checkSql)) {

            check.setString(1, name);
            ResultSet rs = check.executeQuery();

            if (rs.next()) {
                PreparedStatement update = conn.prepareStatement(updateSql);
                update.setInt(1, totalBeds);
                update.setString(2, name);
                update.executeUpdate();
            } else {
                PreparedStatement insert = conn.prepareStatement(insertSql);
                insert.setString(1, name);
                insert.setInt(2, totalBeds);
                insert.executeUpdate();
            }

        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    public static boolean occupyBed(String wardName) {
        try (Connection conn = DatabaseManager.getConnection()) {
            String query = "SELECT total_beds, occupied_beds FROM wards WHERE name = ?";
            PreparedStatement stmt = conn.prepareStatement(query);
            stmt.setString(1, wardName);
            ResultSet rs = stmt.executeQuery();

            if (rs.next()) {
                int total = rs.getInt("total_beds");
                int occupied = rs.getInt("occupied_beds");
                if (occupied < total) {
                    PreparedStatement update = conn.prepareStatement("UPDATE wards SET occupied_beds = ? WHERE name = ?");
                    update.setInt(1, occupied + 1);
                    update.setString(2, wardName);
                    update.executeUpdate();
                    return true;
                }
            }

        } catch (SQLException e) {
            e.printStackTrace();
        }
        return false;
    }

    public static void releaseBed(String wardName) {
        try (Connection conn = DatabaseManager.getConnection()) {
            String sql = "UPDATE wards SET occupied_beds = occupied_beds - 1 WHERE name = ? AND occupied_beds > 0";
            PreparedStatement stmt = conn.prepareStatement(sql);
            stmt.setString(1, wardName);
            stmt.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
}
