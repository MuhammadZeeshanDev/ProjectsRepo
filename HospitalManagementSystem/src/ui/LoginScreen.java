package ui;

import service.AuthService;

import javax.swing.*;
import java.awt.*;

public class LoginScreen extends JFrame {

    public LoginScreen() {
        setTitle("Hospital Management System");
        setSize(500, 320);
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setResizable(false);
        setLayout(new BorderLayout());

        applyModernStyle();

        JLabel titleLabel = new JLabel("Hospital Management System", JLabel.CENTER);
        titleLabel.setFont(new Font("Segoe UI", Font.BOLD, 22));
        titleLabel.setBorder(BorderFactory.createEmptyBorder(20, 0, 10, 0));
        add(titleLabel, BorderLayout.NORTH);

        JPanel centerPanel = new JPanel(new GridLayout(5, 2, 10, 10));
        centerPanel.setBorder(BorderFactory.createEmptyBorder(10, 50, 10, 50));

        JLabel roleLabel = new JLabel("Select Role:");
        JLabel userLabel = new JLabel("Username:");
        JLabel passLabel = new JLabel("Password:");

        String[] roles = {"Patient", "Admin"};
        JComboBox<String> roleBox = new JComboBox<>(roles);
        JTextField userField = new JTextField();
        JPasswordField passField = new JPasswordField();
        JCheckBox showPassword = new JCheckBox("Show Password");

        JButton loginBtn = new JButton("Continue");

        centerPanel.add(roleLabel);
        centerPanel.add(roleBox);
        centerPanel.add(userLabel);
        centerPanel.add(userField);
        centerPanel.add(passLabel);
        centerPanel.add(passField);
        centerPanel.add(new JLabel());
        centerPanel.add(showPassword);
        centerPanel.add(new JLabel());
        centerPanel.add(loginBtn);

        add(centerPanel, BorderLayout.CENTER);

        // Show/hide password toggle
        showPassword.addActionListener(e -> {
            if (showPassword.isSelected()) {
                passField.setEchoChar((char) 0);
            } else {
                passField.setEchoChar('•');
            }
        });

        // Hide username/password by default for patient
        roleBox.addActionListener(e -> {
            boolean isAdmin = roleBox.getSelectedItem().equals("Admin");
            userLabel.setVisible(isAdmin);
            userField.setVisible(isAdmin);
            passLabel.setVisible(isAdmin);
            passField.setVisible(isAdmin);
            showPassword.setVisible(isAdmin);
        });

        roleBox.setSelectedIndex(0); // Default selection = Patient

        loginBtn.addActionListener(e -> {
            String role = roleBox.getSelectedItem().toString();
            if (role.equals("Admin")) {
                String username = userField.getText().trim();
                String password = new String(passField.getPassword());

                if (AuthService.validateAdmin(username, password)) {
                    new AdminDashboard().setVisible(true);
                    dispose();
                } else {
                    JOptionPane.showMessageDialog(this, "❌ Invalid admin credentials.");
                }
            } else {
                String patientName = JOptionPane.showInputDialog(this, "Enter your name:");
                if (patientName != null && !patientName.trim().isEmpty()) {
                    new PatientDashboard(patientName).setVisible(true);
                    dispose();
                } else {
                    JOptionPane.showMessageDialog(this, "⚠️ Please enter a valid name.");
                }
            }
        });
    }

    private void applyModernStyle() {
        Font font = new Font("Segoe UI", Font.PLAIN, 14);
        UIManager.put("Label.font", font);
        UIManager.put("Button.font", font);
        UIManager.put("TextField.font", font);
        UIManager.put("ComboBox.font", font);
        UIManager.put("PasswordField.font", font);
        UIManager.put("CheckBox.font", font);
    }
}
