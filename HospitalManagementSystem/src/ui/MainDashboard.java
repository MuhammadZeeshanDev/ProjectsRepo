package ui;

import service.AppointmentService;
import service.DoctorService;
import service.EmergencyService;
import service.OPDService;
import service.PatientService;
import service.WardService;
import util.Theme;

import javax.swing.*;
import java.awt.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * The main window shown after a successful login. It has a sidebar to
 * switch between OPD, Emergency, Wards, Appointments, and Doctors, and a
 * top bar showing who is logged in plus the live current date/time.
 */
public class MainDashboard extends JFrame {

    private final CardLayout cardLayout = new CardLayout();
    private final JPanel contentPanel = new JPanel(cardLayout);
    private JLabel clockLabel;

    private static final String CARD_OPD = "OPD";
    private static final String CARD_EMERGENCY = "EMERGENCY";
    private static final String CARD_WARDS = "WARDS";
    private static final String CARD_APPOINTMENTS = "APPOINTMENTS";
    private static final String CARD_DOCTORS = "DOCTORS";

    public MainDashboard(String loggedInUser) {
        setTitle("City Care Hospital - Reception Desk");
        setSize(1150, 700);
        setMinimumSize(new Dimension(1000, 620));
        setLocationRelativeTo(null);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        JPanel root = new JPanel(new BorderLayout());
        root.setBackground(Theme.BACKGROUND);
        setContentPane(root);

        root.add(buildTopBar(loggedInUser), BorderLayout.NORTH);
        root.add(buildSidebar(), BorderLayout.WEST);

        // These services are created once and shared by every panel below,
        // so that a patient registered in OPD (for example) is immediately
        // visible everywhere else too - Emergency, Wards, Appointments.
        PatientService patientService = new PatientService();
        DoctorService doctorService = new DoctorService();
        OPDService opdService = new OPDService();
        EmergencyService emergencyService = new EmergencyService();
        WardService wardService = new WardService();
        AppointmentService appointmentService = new AppointmentService();

        contentPanel.setBackground(Theme.BACKGROUND);
        contentPanel.add(new OPDPanel(patientService, doctorService, opdService, emergencyService), CARD_OPD);
        contentPanel.add(new EmergencyPanel(patientService, doctorService, emergencyService, wardService), CARD_EMERGENCY);
        contentPanel.add(new WardPanel(wardService), CARD_WARDS);
        contentPanel.add(new AppointmentPanel(patientService, doctorService, appointmentService), CARD_APPOINTMENTS);
        contentPanel.add(new DoctorPanel(doctorService), CARD_DOCTORS);
        root.add(contentPanel, BorderLayout.CENTER);

        cardLayout.show(contentPanel, CARD_OPD);
        startLiveClock();
    }

    private JPanel buildTopBar(String loggedInUser) {
        JPanel topBar = new JPanel(new BorderLayout());
        topBar.setBackground(Theme.PRIMARY);
        topBar.setPreferredSize(new Dimension(0, 56));
        topBar.setBorder(BorderFactory.createEmptyBorder(0, 20, 0, 20));

        JLabel title = new JLabel("City Care Hospital");
        title.setFont(Theme.FONT_HEADING);
        title.setForeground(Color.WHITE);

        JPanel right = new JPanel(new FlowLayout(FlowLayout.RIGHT, 20, 0));
        right.setOpaque(false);

        clockLabel = new JLabel();
        clockLabel.setFont(Theme.FONT_NORMAL);
        clockLabel.setForeground(new Color(220, 232, 240));

        JLabel userLabel = new JLabel("Logged in as: " + loggedInUser);
        userLabel.setFont(Theme.FONT_NORMAL);
        userLabel.setForeground(Color.WHITE);

        JButton logoutButton = new JButton("Log Out");
        logoutButton.setFont(Theme.FONT_LABEL);
        logoutButton.setBackground(Theme.PRIMARY_DARK);
        logoutButton.setForeground(Color.WHITE);
        logoutButton.setFocusPainted(false);
        logoutButton.setBorder(BorderFactory.createEmptyBorder(6, 14, 6, 14));
        logoutButton.setCursor(new Cursor(Cursor.HAND_CURSOR));
        logoutButton.addActionListener(e -> logout());

        right.add(clockLabel);
        right.add(userLabel);
        right.add(logoutButton);

        topBar.add(title, BorderLayout.WEST);
        topBar.add(right, BorderLayout.EAST);
        return topBar;
    }

    private JPanel buildSidebar() {
        JPanel sidebar = new JPanel();
        sidebar.setBackground(Theme.PRIMARY_DARK);
        sidebar.setPreferredSize(new Dimension(210, 0));
        sidebar.setLayout(new BoxLayout(sidebar, BoxLayout.Y_AXIS));
        sidebar.setBorder(BorderFactory.createEmptyBorder(20, 0, 0, 0));

        JButton opdButton = createSidebarButton("OPD (Check-ups)");
        JButton emergencyButton = createSidebarButton("Emergency");
        JButton wardsButton = createSidebarButton("Wards");
        JButton appointmentsButton = createSidebarButton("Appointments");
        JButton doctorsButton = createSidebarButton("Doctors");

        opdButton.addActionListener(e -> cardLayout.show(contentPanel, CARD_OPD));
        emergencyButton.addActionListener(e -> cardLayout.show(contentPanel, CARD_EMERGENCY));
        wardsButton.addActionListener(e -> cardLayout.show(contentPanel, CARD_WARDS));
        appointmentsButton.addActionListener(e -> cardLayout.show(contentPanel, CARD_APPOINTMENTS));
        doctorsButton.addActionListener(e -> cardLayout.show(contentPanel, CARD_DOCTORS));

        sidebar.add(opdButton);
        sidebar.add(Box.createVerticalStrut(4));
        sidebar.add(emergencyButton);
        sidebar.add(Box.createVerticalStrut(4));
        sidebar.add(wardsButton);
        sidebar.add(Box.createVerticalStrut(4));
        sidebar.add(appointmentsButton);
        sidebar.add(Box.createVerticalStrut(4));
        sidebar.add(doctorsButton);
        sidebar.add(Box.createVerticalGlue());

        return sidebar;
    }

    private JButton createSidebarButton(String text) {
        JButton button = new JButton(text);
        button.setFont(Theme.FONT_LABEL);
        button.setForeground(Color.WHITE);
        button.setBackground(Theme.PRIMARY_DARK);
        button.setAlignmentX(Component.LEFT_ALIGNMENT);
        button.setMaximumSize(new Dimension(Integer.MAX_VALUE, 46));
        button.setHorizontalAlignment(SwingConstants.LEFT);
        button.setBorder(BorderFactory.createEmptyBorder(10, 24, 10, 10));
        button.setFocusPainted(false);
        button.setCursor(new Cursor(Cursor.HAND_CURSOR));
        button.setBorderPainted(false);
        button.setOpaque(true);
        return button;
    }

    private void startLiveClock() {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("EEEE, dd MMM yyyy   HH:mm:ss");
        Timer timer = new Timer(1000, e -> clockLabel.setText(LocalDateTime.now().format(formatter)));
        timer.setInitialDelay(0);
        timer.start();
    }

    private void logout() {
        int choice = JOptionPane.showConfirmDialog(this, "Log out of the reception desk?",
                "Confirm Logout", JOptionPane.YES_NO_OPTION);
        if (choice == JOptionPane.YES_OPTION) {
            dispose();
            SwingUtilities.invokeLater(() -> new LoginScreen().setVisible(true));
        }
    }
}
