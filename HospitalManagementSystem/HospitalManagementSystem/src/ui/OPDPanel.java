package ui;

import model.Doctor;
import model.OPDVisit;
import model.Patient;
import service.DoctorService;
import service.EmergencyService;
import service.OPDService;
import service.PatientService;
import util.Theme;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.awt.event.ComponentAdapter;
import java.awt.event.ComponentEvent;
import java.util.List;

/**
 * OPD desk: where a patient walking in for a routine/general check-up is
 * registered. If the doctor decides the case is actually serious, the
 * visit can be referred straight into the Emergency tab from here.
 */
public class OPDPanel extends JPanel {

    private final PatientService patientService;
    private final DoctorService doctorService;
    private final OPDService opdService;
    private final EmergencyService emergencyService;

    private JTextField nameField;
    private JSpinner ageSpinner;
    private JComboBox<String> genderCombo;
    private JTextField phoneField;
    private JTextField addressField;
    private JComboBox<DoctorOption> doctorCombo;
    private JTextField symptomsField;

    private JTable table;
    private DefaultTableModel tableModel;

    public OPDPanel(PatientService patientService, DoctorService doctorService,
                     OPDService opdService, EmergencyService emergencyService) {
        this.patientService = patientService;
        this.doctorService = doctorService;
        this.opdService = opdService;
        this.emergencyService = emergencyService;

        setLayout(new BorderLayout(16, 16));
        setBorder(BorderFactory.createEmptyBorder(16, 16, 16, 16));
        setBackground(Theme.BACKGROUND);

        add(buildFormPanel(), BorderLayout.WEST);
        add(buildTablePanel(), BorderLayout.CENTER);

        refreshTable(opdService.getActiveVisits());

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

        JLabel heading = new JLabel("OPD - Register Check-up");
        heading.setFont(Theme.FONT_HEADING);
        heading.setForeground(Theme.TEXT_DARK);
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
        doctorCombo = new JComboBox<>();
        reloadDoctorOptions();
        symptomsField = new JTextField();

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
        form.add(formLabel("Attending Doctor"));
        form.add(spaced(doctorCombo));
        form.add(formLabel("Symptoms / Complaint"));
        form.add(spaced(symptomsField));

        JButton registerButton = new JButton("Register OPD Visit");
        Theme.stylePrimaryButton(registerButton);
        registerButton.setAlignmentX(Component.LEFT_ALIGNMENT);
        registerButton.addActionListener(e -> registerVisit());

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
        JButton activeButton = new JButton("Active Visits");
        JButton allButton = new JButton("All Visits");
        Theme.stylePrimaryButton(activeButton);
        Theme.styleSecondaryButton(allButton);
        activeButton.addActionListener(e -> refreshTable(opdService.getActiveVisits()));
        allButton.addActionListener(e -> refreshTable(opdService.getAllVisits()));
        filterBar.add(activeButton);
        filterBar.add(allButton);

        tableModel = new DefaultTableModel(
                new String[]{"OPD ID", "Patient", "Age", "Gender", "Doctor", "Department",
                        "Symptoms", "Visit Date", "Status"}, 0) {
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

        JButton dischargeButton = new JButton("Mark as Discharged");
        Theme.styleAccentButton(dischargeButton);
        dischargeButton.addActionListener(e -> dischargeSelected());

        JButton referButton = new JButton("Refer to Emergency");
        Theme.styleDangerButton(referButton);
        referButton.addActionListener(e -> referSelectedToEmergency());

        JPanel bottomBar = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 8));
        bottomBar.setBackground(Theme.BACKGROUND);
        bottomBar.add(dischargeButton);
        bottomBar.add(referButton);

        outer.add(filterBar, BorderLayout.NORTH);
        outer.add(scrollPane, BorderLayout.CENTER);
        outer.add(bottomBar, BorderLayout.SOUTH);
        return outer;
    }

    private void registerVisit() {
        String name = nameField.getText().trim();
        String phone = phoneField.getText().trim();
        String address = addressField.getText().trim();
        String symptoms = symptomsField.getText().trim();
        int age = (Integer) ageSpinner.getValue();
        String gender = (String) genderCombo.getSelectedItem();
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
        opdService.registerVisit(patient.getPatientId(), patient.getName(), age, gender,
                doctorOption.doctor.getName(), doctorOption.doctor.getDepartment(), symptoms);

        JOptionPane.showMessageDialog(this, "OPD visit registered for " + patient.getName()
                + " (Patient ID: " + patient.getPatientId() + ").");

        nameField.setText("");
        ageSpinner.setValue(1);
        genderCombo.setSelectedIndex(0);
        phoneField.setText("");
        addressField.setText("");
        symptomsField.setText("");
        refreshTable(opdService.getActiveVisits());
    }

    private void dischargeSelected() {
        String opdId = getSelectedOpdId();
        if (opdId == null) {
            return;
        }
        OPDVisit visit = opdService.findById(opdId);
        if (visit == null || !visit.getStatus().equals("Under Treatment")) {
            JOptionPane.showMessageDialog(this, "This visit has already been closed.",
                    "Cannot update", JOptionPane.WARNING_MESSAGE);
            return;
        }
        opdService.updateStatus(opdId, "Discharged");
        refreshTable(opdService.getActiveVisits());
    }

    private void referSelectedToEmergency() {
        String opdId = getSelectedOpdId();
        if (opdId == null) {
            return;
        }
        OPDVisit visit = opdService.findById(opdId);
        if (visit == null || !visit.getStatus().equals("Under Treatment")) {
            JOptionPane.showMessageDialog(this, "This visit has already been closed.",
                    "Cannot update", JOptionPane.WARNING_MESSAGE);
            return;
        }
        int choice = JOptionPane.showConfirmDialog(this,
                "Refer " + visit.getPatientName() + " to the Emergency department?",
                "Confirm Referral", JOptionPane.YES_NO_OPTION);
        if (choice != JOptionPane.YES_OPTION) {
            return;
        }
        emergencyService.registerCase(visit.getPatientId(), visit.getPatientName(), visit.getAge(),
                visit.getGender(), "Serious", visit.getDoctorName(), visit.getDepartment());
        opdService.updateStatus(opdId, "Referred to Emergency");
        refreshTable(opdService.getActiveVisits());
        JOptionPane.showMessageDialog(this, "Patient referred to Emergency. Check the Emergency tab.");
    }

    private String getSelectedOpdId() {
        int row = table.getSelectedRow();
        if (row == -1) {
            JOptionPane.showMessageDialog(this, "Select a visit from the table first.",
                    "No visit selected", JOptionPane.WARNING_MESSAGE);
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

    private void refreshTable(List<OPDVisit> visits) {
        tableModel.setRowCount(0);
        for (OPDVisit v : visits) {
            tableModel.addRow(new Object[]{
                    v.getOpdId(), v.getPatientName(), v.getAge(), v.getGender(), v.getDoctorName(),
                    v.getDepartment(), v.getSymptoms(), v.getVisitDate(), v.getStatus()
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
