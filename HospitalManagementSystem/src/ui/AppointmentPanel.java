package ui;

import model.Appointment;
import model.Doctor;
import model.Patient;
import service.AppointmentService;
import service.DoctorService;
import service.PatientService;
import util.Theme;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.awt.event.ComponentAdapter;
import java.awt.event.ComponentEvent;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Date;
import java.util.List;

/**
 * Appointments desk: books a future visit for a patient who is already
 * registered (through OPD or Emergency) with a doctor picked from the
 * Doctors master list. The date/time picker defaults to the real current
 * date and time and cannot be set to a moment that has already passed,
 * but any date from today onward can be chosen for upcoming visits.
 */
public class AppointmentPanel extends JPanel {

    private final PatientService patientService;
    private final DoctorService doctorService;
    private final AppointmentService appointmentService;

    private JTextField patientSearchField;
    private JComboBox<PatientOption> patientCombo;
    private JComboBox<DoctorOption> doctorCombo;
    private JLabel departmentValueLabel;
    private JSpinner dateSpinner;
    private JSpinner timeSpinner;
    private JTextField reasonField;
    private JLabel liveClockLabel;

    private JTable table;
    private DefaultTableModel tableModel;

    public AppointmentPanel(PatientService patientService, DoctorService doctorService,
                             AppointmentService appointmentService) {
        this.patientService = patientService;
        this.doctorService = doctorService;
        this.appointmentService = appointmentService;

        setLayout(new BorderLayout(16, 16));
        setBorder(BorderFactory.createEmptyBorder(16, 16, 16, 16));
        setBackground(Theme.BACKGROUND);

        add(buildFormPanel(), BorderLayout.WEST);
        add(buildTablePanel(), BorderLayout.CENTER);

        refreshTable(appointmentService.getUpcomingAppointments());
        startLiveClock();

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
        outer.setPreferredSize(new Dimension(340, 0));
        outer.setBorder(BorderFactory.createLineBorder(Theme.BORDER));

        JLabel heading = new JLabel("Book Appointment");
        heading.setFont(Theme.FONT_HEADING);
        heading.setForeground(Theme.TEXT_DARK);
        heading.setBorder(BorderFactory.createEmptyBorder(16, 16, 8, 16));

        JPanel form = new JPanel();
        form.setLayout(new BoxLayout(form, BoxLayout.Y_AXIS));
        form.setBackground(Theme.PANEL_BACKGROUND);
        form.setBorder(BorderFactory.createEmptyBorder(0, 16, 16, 16));

        liveClockLabel = new JLabel();
        liveClockLabel.setFont(new Font("Segoe UI", Font.ITALIC, 12));
        liveClockLabel.setForeground(Theme.TEXT_MUTED);
        liveClockLabel.setAlignmentX(Component.LEFT_ALIGNMENT);

        patientSearchField = new JTextField();
        JButton findButton = new JButton("Find Patient (name / phone / ID)");
        Theme.styleSecondaryButton(findButton);
        findButton.setAlignmentX(Component.LEFT_ALIGNMENT);
        findButton.addActionListener(e -> searchPatients());
        patientSearchField.addActionListener(e -> searchPatients());

        patientCombo = new JComboBox<>();

        doctorCombo = new JComboBox<>();
        reloadDoctorOptions();
        doctorCombo.addActionListener(e -> updateDepartmentLabel());

        departmentValueLabel = new JLabel("-");
        departmentValueLabel.setFont(Theme.FONT_NORMAL);
        departmentValueLabel.setForeground(Theme.TEXT_MUTED);
        departmentValueLabel.setAlignmentX(Component.LEFT_ALIGNMENT);

        dateSpinner = new JSpinner(new SpinnerDateModel());
        dateSpinner.setEditor(new JSpinner.DateEditor(dateSpinner, "yyyy-MM-dd"));
        dateSpinner.setValue(toDate(LocalDate.now()));

        timeSpinner = new JSpinner(new SpinnerDateModel());
        timeSpinner.setEditor(new JSpinner.DateEditor(timeSpinner, "HH:mm"));
        timeSpinner.setValue(toDate(LocalTime.now()));

        reasonField = new JTextField();

        form.add(liveClockLabel);
        form.add(Box.createVerticalStrut(10));
        form.add(formLabel("Search Registered Patient"));
        form.add(spaced(patientSearchField));
        form.add(Box.createVerticalStrut(6));
        form.add(findButton);
        form.add(formLabel("Patient"));
        form.add(spaced(patientCombo));
        form.add(formLabel("Doctor"));
        form.add(spaced(doctorCombo));
        form.add(formLabel("Department"));
        form.add(departmentValueLabel);
        form.add(formLabel("Appointment Date"));
        form.add(spaced(dateSpinner));
        form.add(formLabel("Appointment Time"));
        form.add(spaced(timeSpinner));
        form.add(formLabel("Reason for Visit"));
        form.add(spaced(reasonField));

        JButton bookButton = new JButton("Book Appointment");
        Theme.stylePrimaryButton(bookButton);
        bookButton.setAlignmentX(Component.LEFT_ALIGNMENT);
        bookButton.addActionListener(e -> bookAppointment());

        form.add(Box.createVerticalStrut(16));
        form.add(rowOf(bookButton));

        updateDepartmentLabel();

        outer.add(heading, BorderLayout.NORTH);
        outer.add(form, BorderLayout.CENTER);
        return outer;
    }

    private JPanel buildTablePanel() {
        JPanel outer = new JPanel(new BorderLayout(0, 10));
        outer.setBackground(Theme.BACKGROUND);

        JPanel filterBar = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        filterBar.setBackground(Theme.BACKGROUND);

        JButton todayButton = new JButton("Today's Appointments");
        JButton upcomingButton = new JButton("Upcoming Appointments");
        JButton allButton = new JButton("All Appointments");
        Theme.stylePrimaryButton(todayButton);
        Theme.styleSecondaryButton(upcomingButton);
        Theme.styleSecondaryButton(allButton);

        todayButton.addActionListener(e -> refreshTable(appointmentService.getAppointmentsByDate(LocalDate.now())));
        upcomingButton.addActionListener(e -> refreshTable(appointmentService.getUpcomingAppointments()));
        allButton.addActionListener(e -> refreshTable(appointmentService.getAllAppointments()));

        filterBar.add(todayButton);
        filterBar.add(upcomingButton);
        filterBar.add(allButton);

        tableModel = new DefaultTableModel(
                new String[]{"Appt ID", "Date", "Time", "Patient", "Doctor", "Department", "Reason", "Status"}, 0) {
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

        JButton cancelButton = new JButton("Cancel Selected Appointment");
        Theme.styleDangerButton(cancelButton);
        cancelButton.addActionListener(e -> cancelSelectedAppointment());

        JPanel bottomBar = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 8));
        bottomBar.setBackground(Theme.BACKGROUND);
        bottomBar.add(cancelButton);

        outer.add(filterBar, BorderLayout.NORTH);
        outer.add(scrollPane, BorderLayout.CENTER);
        outer.add(bottomBar, BorderLayout.SOUTH);
        return outer;
    }

    private void searchPatients() {
        String keyword = patientSearchField.getText().trim();
        patientCombo.removeAllItems();
        List<Patient> results = keyword.isEmpty()
                ? patientService.getAllPatients()
                : patientService.search(keyword);
        if (results.isEmpty()) {
            JOptionPane.showMessageDialog(this,
                    "No registered patient matched that search. Patients must first be registered "
                            + "through the OPD or Emergency tab.",
                    "No results", JOptionPane.INFORMATION_MESSAGE);
            return;
        }
        for (Patient p : results) {
            patientCombo.addItem(new PatientOption(p));
        }
    }

    private void bookAppointment() {
        PatientOption selectedPatient = (PatientOption) patientCombo.getSelectedItem();
        DoctorOption selectedDoctor = (DoctorOption) doctorCombo.getSelectedItem();
        String reason = reasonField.getText().trim();

        LocalDate date = toLocalDate((Date) dateSpinner.getValue());
        LocalTime time = toLocalTime((Date) timeSpinner.getValue());

        if (selectedPatient == null) {
            JOptionPane.showMessageDialog(this,
                    "Search for and select a registered patient first.",
                    "No patient selected", JOptionPane.WARNING_MESSAGE);
            return;
        }
        if (selectedDoctor == null) {
            JOptionPane.showMessageDialog(this, "No doctors available. Please add a doctor first.",
                    "Missing doctor", JOptionPane.WARNING_MESSAGE);
            return;
        }

        LocalDateTime chosenMoment = LocalDateTime.of(date, time);
        if (chosenMoment.isBefore(LocalDateTime.now())) {
            JOptionPane.showMessageDialog(this,
                    "The chosen date/time has already passed. Please pick the current time or a time in the future.",
                    "Invalid date/time", JOptionPane.WARNING_MESSAGE);
            return;
        }

        Appointment appointment = appointmentService.bookAppointment(
                selectedPatient.patient.getPatientId(), selectedPatient.patient.getName(),
                selectedDoctor.doctor.getName(), selectedDoctor.doctor.getDepartment(), date, time, reason);

        if (appointment == null) {
            JOptionPane.showMessageDialog(this,
                    selectedDoctor.doctor.getName() + " already has an appointment at that exact date and time.\n"
                            + "Please choose a different time.",
                    "Time slot unavailable", JOptionPane.WARNING_MESSAGE);
            return;
        }

        JOptionPane.showMessageDialog(this, "Appointment booked successfully (ID: "
                + appointment.getAppointmentId() + ").");
        reasonField.setText("");
        refreshTable(appointmentService.getUpcomingAppointments());
    }

    private void cancelSelectedAppointment() {
        int row = table.getSelectedRow();
        if (row == -1) {
            JOptionPane.showMessageDialog(this, "Select an appointment from the table first.",
                    "No appointment selected", JOptionPane.WARNING_MESSAGE);
            return;
        }
        String appointmentId = (String) tableModel.getValueAt(row, 0);
        int choice = JOptionPane.showConfirmDialog(this, "Cancel this appointment?",
                "Confirm Cancel", JOptionPane.YES_NO_OPTION);
        if (choice == JOptionPane.YES_OPTION) {
            appointmentService.cancelAppointment(appointmentId);
            refreshTable(appointmentService.getUpcomingAppointments());
        }
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
        updateDepartmentLabel();
    }

    private void updateDepartmentLabel() {
        if (departmentValueLabel == null) {
            return;
        }
        DoctorOption selected = (DoctorOption) doctorCombo.getSelectedItem();
        departmentValueLabel.setText(selected == null ? "-" : selected.doctor.getDepartment());
    }

    private void refreshTable(List<Appointment> appointments) {
        tableModel.setRowCount(0);
        for (Appointment a : appointments) {
            tableModel.addRow(new Object[]{
                    a.getAppointmentId(), a.getAppointmentDate(), a.getAppointmentTime(),
                    a.getPatientName(), a.getDoctorName(), a.getDepartment(),
                    a.getReason(), a.getStatus()
            });
        }
    }

    private void startLiveClock() {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("EEEE, dd MMM yyyy   HH:mm:ss");
        Timer timer = new Timer(1000, e ->
                liveClockLabel.setText("Right now: " + LocalDateTime.now().format(formatter)));
        timer.setInitialDelay(0);
        timer.start();
    }

    private Date toDate(LocalDate date) {
        return Date.from(date.atStartOfDay(ZoneId.systemDefault()).toInstant());
    }

    private Date toDate(LocalTime time) {
        return Date.from(LocalDate.now().atTime(time).atZone(ZoneId.systemDefault()).toInstant());
    }

    private LocalDate toLocalDate(Date date) {
        return Instant.ofEpochMilli(date.getTime()).atZone(ZoneId.systemDefault()).toLocalDate();
    }

    private LocalTime toLocalTime(Date date) {
        return Instant.ofEpochMilli(date.getTime()).atZone(ZoneId.systemDefault()).toLocalTime()
                .withSecond(0).withNano(0);
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
