package ui;

import service.AuthService;
import util.Theme;

import javax.swing.*;
import java.awt.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * The first screen the receptionist sees. It checks the username and
 * password using AuthService, and if they are correct it opens the
 * main dashboard.
 */
public class LoginScreen extends JFrame {

    private final AuthService authService = new AuthService();
    private JTextField usernameField;
    private JPasswordField passwordField;
    private JLabel clockLabel;

    public LoginScreen() {
        setTitle("Hospital Management System - Login");
        setSize(430, 480);
        setLocationRelativeTo(null);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setResizable(false);

        JPanel root = new JPanel(new BorderLayout());
        root.setBackground(Theme.BACKGROUND);
        setContentPane(root);

        root.add(buildHeader(), BorderLayout.NORTH);
        root.add(buildForm(), BorderLayout.CENTER);
        root.add(buildFooter(), BorderLayout.SOUTH);

        startLiveClock();
    }

    private JPanel buildHeader() {
        JPanel header = new JPanel();
        header.setBackground(Theme.PRIMARY);
        header.setPreferredSize(new Dimension(0, 110));
        header.setLayout(new BoxLayout(header, BoxLayout.Y_AXIS));

        JLabel icon = new JLabel("+");
        icon.setFont(new Font("Segoe UI", Font.BOLD, 30));
        icon.setForeground(Color.WHITE);
        icon.setAlignmentX(Component.CENTER_ALIGNMENT);

        JLabel title = new JLabel("City Care Hospital");
        title.setFont(Theme.FONT_TITLE);
        title.setForeground(Color.WHITE);
        title.setAlignmentX(Component.CENTER_ALIGNMENT);

        JLabel subtitle = new JLabel("Reception Desk Login");
        subtitle.setFont(Theme.FONT_NORMAL);
        subtitle.setForeground(new Color(220, 232, 240));
        subtitle.setAlignmentX(Component.CENTER_ALIGNMENT);

        header.add(Box.createVerticalStrut(14));
        header.add(icon);
        header.add(title);
        header.add(subtitle);
        return header;
    }

    private JPanel buildForm() {
        JPanel wrapper = new JPanel(new GridBagLayout());
        wrapper.setBackground(Theme.BACKGROUND);

        JPanel form = new JPanel(new GridBagLayout());
        form.setBackground(Theme.PANEL_BACKGROUND);
        form.setBorder(BorderFactory.createEmptyBorder(30, 30, 30, 30));

        GridBagConstraints gbc = new GridBagConstraints();
        gbc.gridx = 0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.insets = new Insets(8, 0, 8, 0);

        JLabel userLabel = new JLabel("Username");
        userLabel.setFont(Theme.FONT_LABEL);
        usernameField = new JTextField(18);
        usernameField.setFont(Theme.FONT_NORMAL);

        JLabel passLabel = new JLabel("Password");
        passLabel.setFont(Theme.FONT_LABEL);
        passwordField = new JPasswordField(18);
        passwordField.setFont(Theme.FONT_NORMAL);

        JButton loginButton = new JButton("Log In");
        Theme.stylePrimaryButton(loginButton);
        loginButton.addActionListener(e -> attemptLogin());

        JLabel hint = new JLabel("<html><center>Default login: <b>receptionist</b> / <b>reception123</b></center></html>");
        hint.setFont(new Font("Segoe UI", Font.ITALIC, 11));
        hint.setForeground(Theme.TEXT_MUTED);

        gbc.gridy = 0;
        form.add(userLabel, gbc);
        gbc.gridy = 1;
        form.add(usernameField, gbc);
        gbc.gridy = 2;
        form.add(passLabel, gbc);
        gbc.gridy = 3;
        form.add(passwordField, gbc);
        gbc.gridy = 4;
        gbc.insets = new Insets(20, 0, 8, 0);
        form.add(loginButton, gbc);
        gbc.gridy = 5;
        gbc.insets = new Insets(4, 0, 0, 0);
        form.add(hint, gbc);

        passwordField.addActionListener(e -> attemptLogin());

        wrapper.add(form);
        return wrapper;
    }

    private JPanel buildFooter() {
        JPanel footer = new JPanel();
        footer.setBackground(Theme.BACKGROUND);
        clockLabel = new JLabel();
        clockLabel.setFont(Theme.FONT_NORMAL);
        clockLabel.setForeground(Theme.TEXT_MUTED);
        footer.add(clockLabel);
        return footer;
    }

    private void startLiveClock() {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("EEEE, dd MMM yyyy   HH:mm:ss");
        Timer timer = new Timer(1000, e -> clockLabel.setText(LocalDateTime.now().format(formatter)));
        timer.setInitialDelay(0);
        timer.start();
    }

    private void attemptLogin() {
        String username = usernameField.getText().trim();
        String password = new String(passwordField.getPassword());

        if (username.isEmpty() || password.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter both username and password.",
                    "Missing details", JOptionPane.WARNING_MESSAGE);
            return;
        }

        if (authService.login(username, password)) {
            dispose();
            SwingUtilities.invokeLater(() -> new MainDashboard(username).setVisible(true));
        } else {
            JOptionPane.showMessageDialog(this, "Incorrect username or password.",
                    "Login failed", JOptionPane.ERROR_MESSAGE);
            passwordField.setText("");
        }
    }
}
