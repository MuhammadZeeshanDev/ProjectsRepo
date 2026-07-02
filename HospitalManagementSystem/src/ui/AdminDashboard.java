package ui;

import javax.swing.*;
import java.awt.*;

public class AdminDashboard extends JFrame {

    private JTabbedPane tabbedPane;

    public AdminDashboard() {
        setTitle("Admin Dashboard");
        setSize(1000, 650);
        setLocationRelativeTo(null);
        setDefaultCloseOperation(DISPOSE_ON_CLOSE);
        setLayout(new BorderLayout());
        setResizable(false);

        applyModernStyle();

        JLabel header = new JLabel("Admin Dashboard - Hospital Control Panel", JLabel.CENTER);
        header.setFont(new Font("Segoe UI", Font.BOLD, 20));
        header.setOpaque(true);
        header.setBackground(new Color(0x2E8B57)); // Sea green
        header.setForeground(Color.WHITE);
        header.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        add(header, BorderLayout.NORTH);

        tabbedPane = new JTabbedPane();
        tabbedPane.setFont(new Font("Segoe UI", Font.PLAIN, 14));

        tabbedPane.addTab("🩺 OPD", new OPDPanel());
        tabbedPane.addTab("📅 Appointments", new AppointmentPanel());
        tabbedPane.addTab("🏥 Admissions", new AdmissionsPanel());
        tabbedPane.addTab("🩸 Blood Bank", new BloodBankPanel());
        tabbedPane.addTab("💊 Pharmacy", new PharmacyPanel());
        tabbedPane.addTab("🛏️ Wards", new WardPanel());
        tabbedPane.addTab("⚰️ Deceased", new DeceasedPanel());

        add(tabbedPane, BorderLayout.CENTER);
    }

    private void applyModernStyle() {
        Font font = new Font("Segoe UI", Font.PLAIN, 14);
        UIManager.put("Label.font", font);
        UIManager.put("Button.font", font);
        UIManager.put("TextField.font", font);
        UIManager.put("ComboBox.font", font);
        UIManager.put("PasswordField.font", font);
        UIManager.put("Table.font", font);
        UIManager.put("Table.rowHeight", 22);
    }
}
