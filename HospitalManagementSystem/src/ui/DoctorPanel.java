package ui;

import model.Doctor;
import service.DoctorService;
import util.Departments;
import util.Theme;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.util.List;

/**
 * Screen for managing the hospital's doctors. Every other panel (OPD,
 * Emergency, Appointments) picks a doctor from this same list, so
 * keeping it up to date here keeps the rest of the app consistent.
 */
public class DoctorPanel extends JPanel {

    private final DoctorService doctorService;

    private JTextField nameField;
    private JComboBox<String> departmentCombo;
    private JTextField phoneField;
    private JComboBox<String> statusCombo;

    private JTable table;
    private DefaultTableModel tableModel;
    private String selectedDoctorId = null;

    public DoctorPanel(DoctorService doctorService) {
        this.doctorService = doctorService;
        setLayout(new BorderLayout(16, 16));
        setBorder(BorderFactory.createEmptyBorder(16, 16, 16, 16));
        setBackground(Theme.BACKGROUND);

        add(buildFormPanel(), BorderLayout.WEST);
        add(buildTablePanel(), BorderLayout.CENTER);

        refreshTable();
    }

    private JPanel buildFormPanel() {
        JPanel outer = new JPanel(new BorderLayout());
        outer.setBackground(Theme.PANEL_BACKGROUND);
        outer.setPreferredSize(new Dimension(300, 0));
        outer.setBorder(BorderFactory.createLineBorder(Theme.BORDER));

        JLabel heading = new JLabel("Add / Edit Doctor");
        heading.setFont(Theme.FONT_HEADING);
        heading.setForeground(Theme.TEXT_DARK);
        heading.setBorder(BorderFactory.createEmptyBorder(16, 16, 8, 16));

        JPanel form = new JPanel();
        form.setLayout(new BoxLayout(form, BoxLayout.Y_AXIS));
        form.setBackground(Theme.PANEL_BACKGROUND);
        form.setBorder(BorderFactory.createEmptyBorder(0, 16, 16, 16));

        nameField = new JTextField();
        departmentCombo = new JComboBox<>(Departments.ALL);
        phoneField = new JTextField();
        statusCombo = new JComboBox<>(new String[]{"Available", "On Leave"});

        form.add(formLabel("Doctor Name"));
        form.add(spaced(nameField));
        form.add(formLabel("Department"));
        form.add(spaced(departmentCombo));
        form.add(formLabel("Phone Number"));
        form.add(spaced(phoneField));
        form.add(formLabel("Status"));
        form.add(spaced(statusCombo));

        JButton saveButton = new JButton("Save Doctor");
        Theme.stylePrimaryButton(saveButton);
        saveButton.setAlignmentX(Component.LEFT_ALIGNMENT);
        saveButton.addActionListener(e -> saveOrUpdateDoctor());

        JButton clearButton = new JButton("Clear Form");
        Theme.styleSecondaryButton(clearButton);
        clearButton.setAlignmentX(Component.LEFT_ALIGNMENT);
        clearButton.addActionListener(e -> clearForm());

        JButton deleteButton = new JButton("Delete Selected");
        Theme.styleDangerButton(deleteButton);
        deleteButton.setAlignmentX(Component.LEFT_ALIGNMENT);
        deleteButton.addActionListener(e -> deleteSelectedDoctor());

        form.add(Box.createVerticalStrut(16));
        form.add(rowOf(saveButton, clearButton));
        form.add(Box.createVerticalStrut(8));
        JPanel deleteRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
        deleteRow.setBackground(Theme.PANEL_BACKGROUND);
        deleteRow.setAlignmentX(Component.LEFT_ALIGNMENT);
        deleteRow.add(deleteButton);
        form.add(deleteRow);

        outer.add(heading, BorderLayout.NORTH);
        outer.add(form, BorderLayout.CENTER);
        return outer;
    }

    private JPanel buildTablePanel() {
        JPanel outer = new JPanel(new BorderLayout(0, 10));
        outer.setBackground(Theme.BACKGROUND);

        JLabel heading = new JLabel("All Doctors");
        heading.setFont(Theme.FONT_HEADING);
        heading.setForeground(Theme.TEXT_DARK);

        tableModel = new DefaultTableModel(
                new String[]{"Doctor ID", "Name", "Department", "Phone", "Status"}, 0) {
            @Override
            public boolean isCellEditable(int row, int column) {
                return false;
            }
        };
        table = new JTable(tableModel);
        table.setFont(Theme.FONT_NORMAL);
        table.setRowHeight(26);
        table.getTableHeader().setFont(Theme.FONT_LABEL);
        table.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        table.getSelectionModel().addListSelectionListener(e -> loadSelectedRowIntoForm());

        JScrollPane scrollPane = new JScrollPane(table);
        scrollPane.setBorder(BorderFactory.createLineBorder(Theme.BORDER));

        outer.add(heading, BorderLayout.NORTH);
        outer.add(scrollPane, BorderLayout.CENTER);
        return outer;
    }

    private void saveOrUpdateDoctor() {
        String name = nameField.getText().trim();
        String department = (String) departmentCombo.getSelectedItem();
        String phone = phoneField.getText().trim();
        String status = (String) statusCombo.getSelectedItem();

        if (name.isEmpty() || phone.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Doctor name and phone number are required.",
                    "Missing details", JOptionPane.WARNING_MESSAGE);
            return;
        }

        if (selectedDoctorId == null) {
            doctorService.addDoctor(name, department, phone);
            JOptionPane.showMessageDialog(this, "Doctor added successfully.");
        } else {
            doctorService.updateDoctor(selectedDoctorId, name, department, phone, status);
            JOptionPane.showMessageDialog(this, "Doctor details updated.");
        }

        clearForm();
        refreshTable();
    }

    private void deleteSelectedDoctor() {
        if (selectedDoctorId == null) {
            JOptionPane.showMessageDialog(this, "Select a doctor from the table first.",
                    "No doctor selected", JOptionPane.WARNING_MESSAGE);
            return;
        }
        int choice = JOptionPane.showConfirmDialog(this, "Remove this doctor from the system?",
                "Confirm Delete", JOptionPane.YES_NO_OPTION);
        if (choice == JOptionPane.YES_OPTION) {
            doctorService.deleteDoctor(selectedDoctorId);
            clearForm();
            refreshTable();
        }
    }

    private void loadSelectedRowIntoForm() {
        int row = table.getSelectedRow();
        if (row == -1) {
            return;
        }
        selectedDoctorId = (String) tableModel.getValueAt(row, 0);
        nameField.setText((String) tableModel.getValueAt(row, 1));
        departmentCombo.setSelectedItem(tableModel.getValueAt(row, 2));
        phoneField.setText((String) tableModel.getValueAt(row, 3));
        statusCombo.setSelectedItem(tableModel.getValueAt(row, 4));
    }

    private void clearForm() {
        selectedDoctorId = null;
        nameField.setText("");
        departmentCombo.setSelectedIndex(0);
        phoneField.setText("");
        statusCombo.setSelectedIndex(0);
        table.clearSelection();
    }

    private void refreshTable() {
        tableModel.setRowCount(0);
        List<Doctor> doctors = doctorService.getAllDoctors();
        for (Doctor d : doctors) {
            tableModel.addRow(new Object[]{
                    d.getDoctorId(), d.getName(), d.getDepartment(), d.getPhone(), d.getStatus()
            });
        }
    }

    private JLabel formLabel(String text) {
        JLabel label = new JLabel(text);
        label.setFont(Theme.FONT_LABEL);
        label.setForeground(Theme.TEXT_DARK);
        label.setAlignmentX(Component.LEFT_ALIGNMENT);
        label.setBorder(BorderFactory.createEmptyBorder(8, 0, 4, 0));
        return label;
    }

    private JComponent spaced(JComponent component) {
        component.setAlignmentX(Component.LEFT_ALIGNMENT);
        component.setMaximumSize(new Dimension(Integer.MAX_VALUE, 30));
        return component;
    }

    private JPanel rowOf(JComponent... components) {
        JPanel row = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
        row.setBackground(Theme.PANEL_BACKGROUND);
        row.setAlignmentX(Component.LEFT_ALIGNMENT);
        for (JComponent c : components) {
            row.add(c);
        }
        return row;
    }
}
