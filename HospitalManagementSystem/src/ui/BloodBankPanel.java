package ui;

import db.DatabaseManager;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.sql.*;

public class BloodBankPanel extends JPanel {

    private JTable table;
    private DefaultTableModel model;
    private JTextField typeField, unitsField;

    public BloodBankPanel() {
        setLayout(new BorderLayout());

        model = new DefaultTableModel(new Object[]{"Blood Type", "Units"}, 0);
        table = new JTable(model);
        JScrollPane scroll = new JScrollPane(table);

        // Top form
        JPanel inputPanel = new JPanel(new GridLayout(2, 3, 5, 5));
        typeField = new JTextField();
        unitsField = new JTextField();
        JButton addBtn = new JButton("Add / Update");

        inputPanel.add(new JLabel("Blood Type:"));
        inputPanel.add(typeField);
        inputPanel.add(new JLabel());
        inputPanel.add(new JLabel("Units:"));
        inputPanel.add(unitsField);
        inputPanel.add(addBtn);

        add(scroll, BorderLayout.CENTER);
        add(inputPanel, BorderLayout.SOUTH);

        addBtn.addActionListener(e -> addOrUpdateBlood());

        loadBloodData();
    }

    private void addOrUpdateBlood() {
        String type = typeField.getText().trim().toUpperCase();
        int units;

        try {
            units = Integer.parseInt(unitsField.getText().trim());
        } catch (NumberFormatException ex) {
            JOptionPane.showMessageDialog(this, "Please enter a valid number for units.");
            return;
        }

        try (Connection conn = DatabaseManager.getConnection()) {
            PreparedStatement check = conn.prepareStatement("SELECT * FROM blood_bank WHERE type = ?");
            check.setString(1, type);
            ResultSet rs = check.executeQuery();

            if (rs.next()) {
                PreparedStatement update = conn.prepareStatement("UPDATE blood_bank SET units = ? WHERE type = ?");
                update.setInt(1, units);
                update.setString(2, type);
                update.executeUpdate();
            } else {
                PreparedStatement insert = conn.prepareStatement("INSERT INTO blood_bank (type, units) VALUES (?, ?)");
                insert.setString(1, type);
                insert.setInt(2, units);
                insert.executeUpdate();
            }

            loadBloodData();
            typeField.setText("");
            unitsField.setText("");

        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private void loadBloodData() {
        model.setRowCount(0);
        try (Connection conn = DatabaseManager.getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT * FROM blood_bank")) {
            while (rs.next()) {
                model.addRow(new Object[]{
                        rs.getString("type"),
                        rs.getInt("units")
                });
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
}
