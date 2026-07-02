package ui;

import model.Patient;
import service.PatientService;

import javax.swing.*;
import java.awt.*;
import java.time.LocalDate;

public class PatientPanel extends JFrame {
    private final PatientService patientService = new PatientService();

    public PatientPanel() {
        setTitle("Patient Admission");
        setSize(400, 400);
        setLayout(new GridLayout(7, 2, 5, 5));
        setLocationRelativeTo(null);

        JTextField nameField = new JTextField();
        JTextField ageField = new JTextField();
        JComboBox<String> genderBox = new JComboBox<>(new String[]{"Male", "Female", "Other"});
        JTextField wardField = new JTextField();

        JButton admitBtn = new JButton("Admit Patient");
        JTextArea outputArea = new JTextArea(5, 30);
        outputArea.setEditable(false);

        add(new JLabel("Name:"));
        add(nameField);
        add(new JLabel("Age:"));
        add(ageField);
        add(new JLabel("Gender:"));
        add(genderBox);
        add(new JLabel("Ward:"));
        add(wardField);
        add(admitBtn);
        add(new JLabel());
        add(new JScrollPane(outputArea));

        admitBtn.addActionListener(e -> {
            String name = nameField.getText();
            int age = Integer.parseInt(ageField.getText());
            String gender = genderBox.getSelectedItem().toString();
            String ward = wardField.getText();
            String date = LocalDate.now().toString();

            Patient p = new Patient(name, age, gender, ward, date);
            patientService.addPatient(p);

            outputArea.setText("Patient Admitted!\n" +
                    "ID: " + p.getId() + "\nName: " + p.getName());
        });
    }
}
