package ui;

import javax.swing.*;
import java.awt.*;

public class Dashboard extends JFrame {
    public Dashboard() {
        setTitle("Hospital Management Dashboard");
        setSize(400, 300);
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new GridLayout(3, 2, 10, 10));

        JButton patientBtn = new JButton("Patient Admission");
        JButton appointmentBtn = new JButton("Appointments");
        JButton inventoryBtn = new JButton("Inventory");
        JButton bloodBankBtn = new JButton("Blood Bank");
        JButton wardBtn = new JButton("Ward Management");

        add(patientBtn);
        add(appointmentBtn);
        add(inventoryBtn);
        add(bloodBankBtn);
        add(wardBtn);

        patientBtn.addActionListener(e -> new PatientPanel().setVisible(true));
    }
}
