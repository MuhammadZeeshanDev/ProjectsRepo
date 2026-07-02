package ui;

import db.DatabaseManager;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.sql.*;
import java.util.UUID;

public class DeceasedPanel extends JPanel {

    private JTable table;
    private DefaultTableModel model;
    private JTextField nameField, dateField, reasonField;

    public DeceasedPanel() {
        setLayout(new BorderLayout());
        setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        model = new DefaultTableModel(new Object[]{"ID", "Name", "Date", "Reason"}, 0);
        table = new JTable(model);
        JScrollPane scrollPane = new JScrollPane(table);

        JPanel form = new JPanel(new GridLayout(4, 2, 10, 10));
        nameField = new JTextField();
        dateField = new JTextField(); // Format: YYYY-MM-DD
        reasonField = new JTextField();

        JButton addBtn = new JButton("➕ Add Deceased");
        JButton deleteBtn = new JButton("❌ Delete Selected");
        JButton refreshBtn = new JButton("🔄 Refresh");

        form.setBorder(BorderFactory.createTitledBorder("Add Deceased Patient"));
        form.add(new JLabel("Name:"));
        form.add(nameField);
        form.add(new JLabel("Date (YYYY-MM-DD):"));
        form.add(dateField);
        form.add(new JLabel("Reason:"));
        form.add(reasonField);
        form.add(addBtn);
        form.add(refreshBtn);

        JPanel bottom = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        bottom.add(deleteBtn);

        add(form, BorderLayout.NORTH);
        add(scrollPane, BorderLayout.CENTER);
        add(bottom, BorderLayout.SOUTH);

        addBtn.addActionListener(e -> addDeceased());
        refreshBtn.addActionListener(e -> loadDeceasedData());
        deleteBtn.addActionListener(e -> deleteSelected());

        loadDeceasedData();
    }

    private void addDeceased() {
        String name = nameField.getText().trim();
        String date = dateField.getText().trim();
        String reason = reasonField.getText().trim();
        String id = UUID.randomUUID().toString();

        if (name.isEmpty() || date.isEmpty() || reason.isEmpty()) {
            JOptionPane.showMessageDialog(this, "All fields are required.");
            return;
        }

        try (Connection conn = DatabaseManager.getConnection()) {
            String sql = "INSERT INTO deceased (id, name, date, reason) VALUES (?, ?, ?, ?)";
            PreparedStatement stmt = conn.prepareStatement(sql);
            stmt.setString(1, id);
            stmt.setString(2, name);
            stmt.setString(3, date);
            stmt.setString(4, reason);
            stmt.executeUpdate();

            nameField.setText("");
            dateField.setText("");
            reasonField.setText("");

            loadDeceasedData();
            JOptionPane.showMessageDialog(this, "Deceased patient added.");
        } catch (SQLException e) {
            e.printStackTrace();
            JOptionPane.showMessageDialog(this, "Error saving data.");
        }
    }

    private void deleteSelected() {
        int row = table.getSelectedRow();
        if (row < 0) {
            JOptionPane.showMessageDialog(this, "Select a row to delete.");
            return;
        }

        String id = model.getValueAt(row, 0).toString();

        try (Connection conn = DatabaseManager.getConnection()) {
            PreparedStatement stmt = conn.prepareStatement("DELETE FROM deceased WHERE id = ?");
            stmt.setString(1, id);
            stmt.executeUpdate();

            loadDeceasedData();
            JOptionPane.showMessageDialog(this, "Deleted successfully.");
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private void loadDeceasedData() {
        model.setRowCount(0);

        try (Connection conn = DatabaseManager.getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT * FROM deceased")) {

            while (rs.next()) {
                model.addRow(new Object[]{
                        rs.getString("id"),
                        rs.getString("name"),
                        rs.getString("date"),
                        rs.getString("reason")
                });
            }

        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
}
