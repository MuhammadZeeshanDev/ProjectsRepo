package ui;

import db.DatabaseManager;
import service.WardService;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.sql.*;
import java.time.LocalDate;
import java.util.UUID;

public class AdmissionsPanel extends JPanel {

    private JTextField nameField, ageField;
    private JComboBox<String> genderBox, wardBox;
    private JTable admittedTable;
    private DefaultTableModel model;

    public AdmissionsPanel() {
        setLayout(new BorderLayout());

        // ✨ Section Header
        JLabel header = new JLabel("Patient Admissions", JLabel.CENTER);
        header.setFont(new Font("Segoe UI", Font.BOLD, 18));
        header.setOpaque(true);
        header.setBackground(new Color(0x2E8B57));
        header.setForeground(Color.WHITE);
        header.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        add(header, BorderLayout.NORTH);

        // 💡 Form section
        JPanel form = new JPanel(new GridLayout(5, 2, 10, 10));
        form.setBorder(BorderFactory.createTitledBorder("Admit New Patient"));

        nameField = new JTextField();
        ageField = new JTextField();
        genderBox = new JComboBox<>(new String[]{"Male", "Female", "Other"});
        wardBox = new JComboBox<>();
        JButton admitBtn = new JButton("Admit Patient");

        form.add(new JLabel("Name:"));
        form.add(nameField);
        form.add(new JLabel("Age:"));
        form.add(ageField);
        form.add(new JLabel("Gender:"));
        form.add(genderBox);
        form.add(new JLabel("Ward:"));
        form.add(wardBox);
        form.add(new JLabel());
        form.add(admitBtn);

        add(form, BorderLayout.WEST);

        // 🧾 Table section
        model = new DefaultTableModel(new Object[]{"ID", "Name", "Ward", "Status", "Date"}, 0);
        admittedTable = new JTable(model);
        admittedTable.setFillsViewportHeight(true);
        admittedTable.getTableHeader().setFont(new Font("Segoe UI", Font.BOLD, 14));

        JScrollPane scroll = new JScrollPane(admittedTable);
        scroll.setBorder(BorderFactory.createTitledBorder("Admitted Patients"));
        add(scroll, BorderLayout.CENTER);

        // 🚪 Discharge button
        JButton dischargeBtn = new JButton("Discharge Selected");
        JPanel bottom = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 10));
        bottom.add(dischargeBtn);
        add(bottom, BorderLayout.SOUTH);

        admitBtn.addActionListener(e -> admitPatient());
        dischargeBtn.addActionListener(e -> dischargePatient());

        loadWardsIntoBox();
        loadAdmittedPatients();
    }

    private void loadWardsIntoBox() {
        wardBox.removeAllItems();
        try (Connection conn = DatabaseManager.getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT name FROM wards")) {
            while (rs.next()) {
                wardBox.addItem(rs.getString("name"));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private void admitPatient() {
        String name = nameField.getText().trim();
        int age;
        try {
            age = Integer.parseInt(ageField.getText().trim());
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(this, "Invalid age.");
            return;
        }

        String gender = genderBox.getSelectedItem().toString();
        String ward = wardBox.getSelectedItem() != null ? wardBox.getSelectedItem().toString() : "";
        String status = "Admitted";
        String date = LocalDate.now().toString();
        String id = UUID.randomUUID().toString();

        if (!WardService.occupyBed(ward)) {
            JOptionPane.showMessageDialog(this, "No beds available in " + ward);
            return;
        }

        try (Connection conn = DatabaseManager.getConnection()) {
            String sql = "INSERT INTO patients (id, name, age, gender, ward, status, date) VALUES (?, ?, ?, ?, ?, ?, ?)";
            PreparedStatement stmt = conn.prepareStatement(sql);
            stmt.setString(1, id);
            stmt.setString(2, name);
            stmt.setInt(3, age);
            stmt.setString(4, gender);
            stmt.setString(5, ward);
            stmt.setString(6, status);
            stmt.setString(7, date);
            stmt.executeUpdate();

            nameField.setText("");
            ageField.setText("");

            loadAdmittedPatients();
            JOptionPane.showMessageDialog(this, "Patient admitted.");
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private void loadAdmittedPatients() {
        model.setRowCount(0);
        try (Connection conn = DatabaseManager.getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT * FROM patients WHERE status = 'Admitted'")) {

            while (rs.next()) {
                model.addRow(new Object[]{
                        rs.getString("id"),
                        rs.getString("name"),
                        rs.getString("ward"),
                        rs.getString("status"),
                        rs.getString("date")
                });
            }

        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private void dischargePatient() {
        int row = admittedTable.getSelectedRow();
        if (row >= 0) {
            String id = model.getValueAt(row, 0).toString();
            String ward = model.getValueAt(row, 2).toString();

            try (Connection conn = DatabaseManager.getConnection()) {
                String sql = "UPDATE patients SET status = 'Discharged' WHERE id = ?";
                PreparedStatement stmt = conn.prepareStatement(sql);
                stmt.setString(1, id);
                stmt.executeUpdate();

                WardService.releaseBed(ward);

                loadAdmittedPatients();
                JOptionPane.showMessageDialog(this, "Patient discharged.");
            } catch (SQLException e) {
                e.printStackTrace();
            }
        } else {
            JOptionPane.showMessageDialog(this, "Please select a patient to discharge.");
        }
    }
}
