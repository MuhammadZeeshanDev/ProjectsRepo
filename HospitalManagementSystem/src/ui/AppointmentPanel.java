package ui;

import db.DatabaseManager;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.sql.*;

public class AppointmentPanel extends JPanel {

    private JTable table;
    private DefaultTableModel model;

    public AppointmentPanel() {
        setLayout(new BorderLayout());

        // Table Model
        model = new DefaultTableModel(
                new Object[]{"ID", "Name", "Age", "Gender", "Date", "Department"}, 0
        );
        table = new JTable(model);
        JScrollPane scrollPane = new JScrollPane(table);
        add(scrollPane, BorderLayout.CENTER);

        // Refresh button
        JButton refreshBtn = new JButton("Refresh Appointments");
        add(refreshBtn, BorderLayout.SOUTH);

        refreshBtn.addActionListener(e -> loadAppointments());

        loadAppointments(); // Load at startup
    }

    private void loadAppointments() {
        model.setRowCount(0); // clear table
        try (Connection conn = DatabaseManager.getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT * FROM appointments")) {

            while (rs.next()) {
                model.addRow(new Object[]{
                        rs.getString("id"),
                        rs.getString("name"),
                        rs.getInt("age"),
                        rs.getString("gender"),
                        rs.getString("date"),
                        rs.getString("department")
                });
            }

        } catch (SQLException e) {
            e.printStackTrace();
            JOptionPane.showMessageDialog(this, "Failed to load appointments.");
        }
    }
}
