package ui;

import model.Doctor;
import model.EmergencyCase;
import model.Patient;
import model.WardAdmission;
import service.DoctorService;
import service.EmergencyService;
import service.PatientService;
import service.WardService;
import util.Theme;
import util.Wards;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.awt.event.ComponentAdapter;
import java.awt.event.ComponentEvent;
import java.util.List;

/**
 * Emergency desk: where a patient in a serious condition is registered.
 * From here a case can be shifted into a ward bed once a doctor decides
 * the patient needs to be admitted, or discharged directly if not.
 */
public class EmergencyPanel extends JPanel {

    private final PatientService patientService;
    private final DoctorService doctorService;
    private final EmergencyService emergencyService;
    private final WardService wardService;

    private JTextField nameField;
    private JSpinner ageSpinner;
    private JComboBox<String> genderCombo;
    private JTextField phoneField;
    private JTextField addressField;
    private JComboBox<String> conditionCombo;
    private JComboBox<DoctorOption> doctorCombo;

    private JTable table;
    private DefaultTableModel tableModel;

    public EmergencyPanel(PatientService patientService, DoctorService doctorService,
                           EmergencyService emergencyService, WardService wardService) {
        this.patientService = patientService;
        this.doctorService = doctorService;
        this.emergencyService = emergencyService;
        this.wardService = wardService;

        setLayout(new BorderLayout(16, 16));
        setBorder(BorderFactory.createEmptyBorder(16, 16, 16, 16));
        setBackground(Theme.BACKGROUND);

        add(buildFormPanel(), BorderLayout.WEST);
        add(buildTablePanel(), BorderLayout.CENTER);

        refreshTable(emergencyService.getActiveCases());

        addComponentListener(new ComponentAdapter() {
            @Override
            public void componentShown(ComponentEvent e) {
                reloadDoctorOptions();
            }
        });
    }

    private JPanel buildFormPanel() {
        JPanel outer = new JPanel(new BorderLayout());
        outer.setBackground(Theme.PANEL_BACKGROUND);
        outer.setPreferredSize(new Dimension(320, 0));
        outer.setBorder(BorderFactory.createLineBorder(Theme.BORDER));

        JLabel heading = new JLabel("Emergency - Register Case");
        heading.setFont(Theme.FONT_HEADING);
        heading.setForeground(Theme.DANGER);
        heading.setBorder(BorderFactory.createEmptyBorder(16, 16, 8, 16));

        JPanel form = new JPanel();
        form.setLayout(new BoxLayout(form, BoxLayout.Y_AXIS));
        form.setBackground(Theme.PANEL_BACKGROUND);
        form.setBorder(BorderFactory.createEmptyBorder(0, 16, 16, 16));

        nameField = new JTextField();
        ageSpinner = new JSpinner(new SpinnerNumberModel(1, 0, 130, 1));
        genderCombo = new JComboBox<>(new String[]{"Male", "Female", "Other"});
        phoneField = new JTextField();
        addressField = new JTextField();
        conditionCombo = new JComboBox<>(new String[]{"Critical", "Serious", "Stable"});
        doctorCombo = new JComboBox<>();
        reloadDoctorOptions();

        form.add(formLabel("Patient Name"));
        form.add(spaced(nameField));
        form.add(formLabel("Age"));
        form.add(spaced(ageSpinner));
        form.add(formLabel("Gender"));
        form.add(spaced(genderCombo));
        form.add(formLabel("Phone Number"));
        form.add(spaced(phoneField));
        form.add(formLabel("Address"));
        form.add(spaced(addressField));
        form.add(formLabel("Condition"));
        form.add(spaced(conditionCombo));
        form.add(formLabel("Attending Doctor"));
        form.add(spaced(doctorCombo));

        JButton registerButton = new JButton("Register Emergency Case");
        Theme.styleDangerButton(registerButton);
        registerButton.setAlignmentX(Component.LEFT_ALIGNMENT);
        registerButton.addActionListener(e -> registerCase());

        form.add(Box.createVerticalStrut(16));
        form.add(rowOf(registerButton));

        outer.add(heading, BorderLayout.NORTH);
        outer.add(form, BorderLayout.CENTER);
        return outer;
    }

    private JPanel buildTablePanel() {
        JPanel outer = new JPanel(new BorderLayout(0, 10));
        outer.setBackground(Theme.BACKGROUND);

        JPanel filterBar = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        filterBar.setBackground(Theme.BACKGROUND);
        JButton activeButton = new JButton("Active Cases");
        JButton allButton = new JButton("All Cases");
        Theme.stylePrimaryButton(activeButton);
        Theme.styleSecondaryButton(allButton);
        activeButton.addActionListener(e -> refreshTable(emergencyService.getActiveCases()));
        allButton.addActionListener(e -> refreshTable(emergencyService.getAllCases()));
        filterBar.add(activeButton);
        filterBar.add(allButton);

        tableModel = new DefaultTableModel(
                new String[]{"Emergency ID", "Patient", "Age", "Gender", "Condition", "Doctor",
                        "Department", "Arrival Date", "Arrival Time", "Status"}, 0) {
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

        JScrollPane scrollPane = new JScrollPane(table);
        scrollPane.setBorder(BorderFactory.createLineBorder(Theme.BORDER));

        JButton shiftButton = new JButton("Shift to Ward");
        Theme.styleAccentButton(shiftButton);
        shiftButton.addActionListener(e -> shiftSelectedToWard());

        JButton dischargeButton = new JButton("Discharge Directly");
        Theme.styleSecondaryButton(dischargeButton);
        dischargeButton.addActionListener(e -> dischargeSelected());

        JPanel bottomBar = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 8));
        bottomBar.setBackground(Theme.BACKGROUND);
        bottomBar.add(shiftButton);
        bottomBar.add(dischargeButton);

        outer.add(filterBar, BorderLayout.NORTH);
        outer.add(scrollPane, BorderLayout.CENTER);
        outer.add(bottomBar, BorderLayout.SOUTH);
        return outer;
    }

    private void registerCase() {
        String name = nameField.getText().trim();
        String phone = phoneField.getText().trim();
        String address = addressField.getText().trim();
        int age = (Integer) ageSpinner.getValue();
        String gender = (String) genderCombo.getSelectedItem();
        String condition = (String) conditionCombo.getSelectedItem();
        DoctorOption doctorOption = (DoctorOption) doctorCombo.getSelectedItem();

        if (name.isEmpty() || phone.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Patient name and phone number are required.",
                    "Missing details", JOptionPane.WARNING_MESSAGE);
            return;
        }
        if (doctorOption == null) {
            JOptionPane.showMessageDialog(this, "No doctors available. Please add a doctor first.",
                    "Missing doctor", JOptionPane.WARNING_MESSAGE);
            return;
        }

        Patient patient = patientService.registerOrFindPatient(name, age, gender, phone, address);
        emergencyService.registerCase(patient.getPatientId(), patient.getName(), age, gender,
                condition, doctorOption.doctor.getName(), doctorOption.doctor.getDepartment());

        JOptionPane.showMessageDialog(this, "Emergency case registered for " + patient.getName()
                + " (Patient ID: " + patient.getPatientId() + ").");

        nameField.setText("");
        ageSpinner.setValue(1);
        genderCombo.setSelectedIndex(0);
        phoneField.setText("");
        addressField.setText("");
        conditionCombo.setSelectedIndex(0);
        refreshTable(emergencyService.getActiveCases());
    }

    private void shiftSelectedToWard() {
        String emergencyId = getSelectedEmergencyId();
        if (emergencyId == null) {
            return;
        }
        EmergencyCase emergencyCase = emergencyService.findById(emergencyId);
        if (emergencyCase == null || !emergencyCase.getStatus().equals("In Emergency")) {
            JOptionPane.showMessageDialog(this, "This case has already been closed.",
                    "Cannot update", JOptionPane.WARNING_MESSAGE);
            return;
        }

        String[] wardNames = Wards.names();
        String[] wardChoices = new String[wardNames.length];
        for (int i = 0; i < wardNames.length; i++) {
            wardChoices[i] = wardNames[i] + "  (" + wardService.availableBeds(wardNames[i]) + " beds free)";
        }

        String selectedChoice = (String) JOptionPane.showInputDialog(this,
                "Choose a ward for " + emergencyCase.getPatientName() + ":",
                "Shift to Ward", JOptionPane.PLAIN_MESSAGE, null, wardChoices, wardChoices[0]);
        if (selectedChoice == null) {
            return; // receptionist cancelled
        }
        int selectedIndex = java.util.Arrays.asList(wardChoices).indexOf(selectedChoice);
        String chosenWard = wardNames[selectedIndex];

        WardAdmission admission = wardService.admitPatient(emergencyCase.getPatientId(), emergencyCase.getPatientName(),
                chosenWard, emergencyCase.getDoctorName(), "Shifted from Emergency (" + emergencyCase.getCondition() + ")");

        if (admission == null) {
            JOptionPane.showMessageDialog(this, chosenWard + " is full. Please choose a different ward.",
                    "Ward full", JOptionPane.WARNING_MESSAGE);
            return;
        }

        emergencyService.updateStatus(emergencyId, "Shifted to Ward");
        refreshTable(emergencyService.getActiveCases());
        JOptionPane.showMessageDialog(this, emergencyCase.getPatientName() + " has been admitted to "
                + chosenWard + ", bed " + admission.getBedNumber() + ". Check the Wards tab.");
    }

    private void dischargeSelected() {
        String emergencyId = getSelectedEmergencyId();
        if (emergencyId == null) {
            return;
        }
        EmergencyCase emergencyCase = emergencyService.findById(emergencyId);
        if (emergencyCase == null || !emergencyCase.getStatus().equals("In Emergency")) {
            JOptionPane.showMessageDialog(this, "This case has already been closed.",
                    "Cannot update", JOptionPane.WARNING_MESSAGE);
            return;
        }
        emergencyService.updateStatus(emergencyId, "Discharged");
        refreshTable(emergencyService.getActiveCases());
    }

    private String getSelectedEmergencyId() {
        int row = table.getSelectedRow();
        if (row == -1) {
            JOptionPane.showMessageDialog(this, "Select a case from the table first.",
                    "No case selected", JOptionPane.WARNING_MESSAGE);
            return null;
        }
        return (String) tableModel.getValueAt(row, 0);
    }

    private void reloadDoctorOptions() {
        DoctorOption previouslySelected = (DoctorOption) doctorCombo.getSelectedItem();
        doctorCombo.removeAllItems();
        List<Doctor> doctors = doctorService.getAllDoctors();
        for (Doctor d : doctors) {
            doctorCombo.addItem(new DoctorOption(d));
        }
        if (previouslySelected != null) {
            for (int i = 0; i < doctorCombo.getItemCount(); i++) {
                if (doctorCombo.getItemAt(i).doctor.getDoctorId().equals(previouslySelected.doctor.getDoctorId())) {
                    doctorCombo.setSelectedIndex(i);
                    break;
                }
            }
        }
    }

    private void refreshTable(List<EmergencyCase> cases) {
        tableModel.setRowCount(0);
        for (EmergencyCase c : cases) {
            tableModel.addRow(new Object[]{
                    c.getEmergencyId(), c.getPatientName(), c.getAge(), c.getGender(), c.getCondition(),
                    c.getDoctorName(), c.getDepartment(), c.getArrivalDate(), c.getArrivalTime(), c.getStatus()
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
