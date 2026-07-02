package ui;

import db.DatabaseManager;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.sql.*;

public class PharmacyPanel extends JPanel {

    private JTable table;
    private DefaultTableModel model;
    private JTextField itemField, qtyField;

    public PharmacyPanel() {
        setLayout(new BorderLayout());

        model = new DefaultTableModel(new Object[]{"Item", "Quantity"}, 0);
        table = new JTable(model);
        JScrollPane scrollPane = new JScrollPane(table);

        JPanel formPanel = new JPanel(new GridLayout(2, 3, 5, 5));
        itemField = new JTextField();
        qtyField = new JTextField();
        JButton addBtn = new JButton("Add / Update");

        formPanel.add(new JLabel("Item Name:"));
        formPanel.add(itemField);
        formPanel.add(new JLabel());
        formPanel.add(new JLabel("Quantity:"));
        formPanel.add(qtyField);
        formPanel.add(addBtn);

        add(scrollPane, BorderLayout.CENTER);
        add(formPanel, BorderLayout.SOUTH);

        addBtn.addActionListener(e -> addOrUpdateItem());

        loadPharmacyData();
    }

    private void addOrUpdateItem() {
        String item = itemField.getText().trim().toLowerCase();
        int qty;

        try {
            qty = Integer.parseInt(qtyField.getText().trim());
        } catch (NumberFormatException e) {
            JOptionPane.showMessageDialog(this, "Enter a valid quantity.");
            return;
        }

        try (Connection conn = DatabaseManager.getConnection()) {
            PreparedStatement check = conn.prepareStatement("SELECT * FROM pharmacy WHERE item = ?");
            check.setString(1, item);
            ResultSet rs = check.executeQuery();

            if (rs.next()) {
                PreparedStatement update = conn.prepareStatement("UPDATE pharmacy SET quantity = ? WHERE item = ?");
                update.setInt(1, qty);
                update.setString(2, item);
                update.executeUpdate();
            } else {
                PreparedStatement insert = conn.prepareStatement("INSERT INTO pharmacy (item, quantity) VALUES (?, ?)");
                insert.setString(1, item);
                insert.setInt(2, qty);
                insert.executeUpdate();
            }

            loadPharmacyData();
            itemField.setText("");
            qtyField.setText("");

        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private void loadPharmacyData() {
        model.setRowCount(0);
        try (Connection conn = DatabaseManager.getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT * FROM pharmacy")) {
            while (rs.next()) {
                model.addRow(new Object[]{
                        rs.getString("item"),
                        rs.getInt("quantity")
                });
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
}
