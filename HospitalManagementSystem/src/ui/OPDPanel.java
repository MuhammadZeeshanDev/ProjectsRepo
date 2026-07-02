package ui;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.util.UUID;
import db.DatabaseManager;
import java.sql.*;

public class OPDPanel extends JPanel {

    private JTextField nameField, ageField, symptomsField;
    private JComboBox<String> genderBox;
    private JTable opdTable;
    private DefaultTableModel model;

    public OPDPanel() {
        setLayout(new BorderLayout());

        // Top Form
        JPanel form = new JPanel(new GridLayout(5, 2, 5, 5));
        nameField = new JTextField();
        ageField = new JTextField();
        genderBox = new JComboBox<>(new String[]{"Male", "Female", "Other"});
        symptomsField = new JTextField();

        JButton addBtn = new JButton("Add to OPD");
        form.add(new JLabel("Name:"));
        form.add(nameField);
        form.add(new JLabel("Age:"));
        form.add(ageField);
        form.add(new JLabel("Gender:"));
        form.add(genderBox);
        form.add(new JLabel("Symptoms:"));
        form.add(symptomsField);
        form.add(new JLabel());
        form.add(addBtn);

        // Table for OPD list
        model = new DefaultTableModel(new Object[]{"ID", "Name", "Age", "Gender", "Symptoms"}, 0);
        opdTable = new JTable(model);
        JScrollPane scroll = new JScrollPane(opdTable);

        // Bottom buttons
        JPanel actionPanel = new JPanel();
        JButton admitBtn = new JButton("Admit");
        JButton rejectBtn = new JButton("Send Home");
        actionPanel.add(admitBtn);
        actionPanel.add(rejectBtn);

        add(form, BorderLayout.NORTH);
        add(scroll, BorderLayout.CENTER);
        add(actionPanel, BorderLayout.SOUTH);

        addBtn.addActionListener(e -> addToOPD());
        admitBtn.addActionListener(e -> admitSelectedPatient());
        rejectBtn.addActionListener(e -> removeSelectedPatient());

        loadOPDData();
    }

    private void addToOPD() {
        String name = nameField.getText().trim();
        int age = Integer.parseInt(ageField.getText().trim());
        String gender = genderBox.getSelectedItem().toString();
        String symptoms = symptomsField.getText().trim();
        String id = UUID.randomUUID().toString();

        try (Connection conn = DatabaseManager.getConnection()) {
            String sql = "INSERT INTO opd (id, name, age, gender, symptoms) VALUES (?, ?, ?, ?, ?)";
            PreparedStatement stmt = conn.prepareStatement(sql);
            stmt.setString(1, id);
            stmt.setString(2, name);
            stmt.setInt(3, age);
            stmt.setString(4, gender);
            stmt.setString(5, symptoms);
            stmt.executeUpdate();
            loadOPDData();
        } catch (Exception ex) {
            ex.printStackTrace();
        }
    }

    private void loadOPDData() {
        model.setRowCount(0);
        try (Connection conn = DatabaseManager.getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT * FROM opd")) {
            while (rs.next()) {
                model.addRow(new Object[]{
                        rs.getString("id"),
                        rs.getString("name"),
                        rs.getInt("age"),
                        rs.getString("gender"),
                        rs.getString("symptoms")
                });
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void admitSelectedPatient() {
        int row = opdTable.getSelectedRow();
        if (row >= 0) {
            String name = model.getValueAt(row, 1).toString();
            String id = model.getValueAt(row, 0).toString();
            JOptionPane.showMessageDialog(this, "Patient " + name + " should now be admitted manually via 'Admissions' tab.");
            deleteOPDEntry(id);
        } else {
            JOptionPane.showMessageDialog(this, "Please select a patient to admit.");
        }
    }

    private void removeSelectedPatient() {
        int row = opdTable.getSelectedRow();
        if (row >= 0) {
            String id = model.getValueAt(row, 0).toString();
            deleteOPDEntry(id);
        }
    }

    private void deleteOPDEntry(String id) {
        try (Connection conn = DatabaseManager.getConnection()) {
            PreparedStatement stmt = conn.prepareStatement("DELETE FROM opd WHERE id = ?");
            stmt.setString(1, id);
            stmt.executeUpdate();
            loadOPDData();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
