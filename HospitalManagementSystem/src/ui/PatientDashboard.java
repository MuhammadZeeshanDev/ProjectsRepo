package ui;

import service.AppointmentService;

import javax.swing.*;
import java.awt.*;

public class PatientDashboard extends JFrame {

    public PatientDashboard(String patientName) {
        setTitle("Patient Dashboard - Welcome " + patientName);
        setSize(400, 400);
        setLocationRelativeTo(null);
        setDefaultCloseOperation(DISPOSE_ON_CLOSE);

        JPanel panel = new JPanel(new GridLayout(7, 2, 5, 5));

        JTextField ageField = new JTextField();
        JComboBox<String> genderBox = new JComboBox<>(new String[]{"Male", "Female", "Other"});
        JTextField dateField = new JTextField("YYYY-MM-DD");
        JTextField deptField = new JTextField();

        JButton bookBtn = new JButton("Book Appointment");
        JTextArea resultArea = new JTextArea(3, 20);
        resultArea.setEditable(false);
        resultArea.setLineWrap(true);

        panel.add(new JLabel("Your Name:"));
        panel.add(new JLabel(patientName));
        panel.add(new JLabel("Age:"));
        panel.add(ageField);
        panel.add(new JLabel("Gender:"));
        panel.add(genderBox);
        panel.add(new JLabel("Preferred Date:"));
        panel.add(dateField);
        panel.add(new JLabel("Department:"));
        panel.add(deptField);
        panel.add(new JLabel());
        panel.add(bookBtn);

        JScrollPane scroll = new JScrollPane(resultArea);

        add(panel, BorderLayout.CENTER);
        add(scroll, BorderLayout.SOUTH);

        bookBtn.addActionListener(e -> {
            try {
                int age = Integer.parseInt(ageField.getText().trim());
                String gender = genderBox.getSelectedItem().toString();
                String date = dateField.getText().trim();
                String dept = deptField.getText().trim();

                boolean success = AppointmentService.bookAppointment(patientName, age, gender, date, dept);
                if (success) {
                    JOptionPane.showMessageDialog(this, "✅ Appointment Booked Successfully!");

                    // Return to main screen
                    dispose(); // Close patient panel
                    new LoginScreen().setVisible(true); // Reopen main login
                } else {
                    resultArea.setText("❌ Booking failed.");
                }
            } catch (Exception ex) {
                resultArea.setText("❗ Invalid input: " + ex.getMessage());
            }
        });
    }
}
