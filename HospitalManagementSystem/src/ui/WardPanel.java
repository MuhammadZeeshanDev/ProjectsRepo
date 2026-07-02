package ui;

import service.WardService;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.util.Map;

public class WardPanel extends JPanel {

    private JTable table;
    private DefaultTableModel model;
    private JTextField wardField, bedField;

    public WardPanel() {
        setLayout(new BorderLayout());

        model = new DefaultTableModel(new Object[]{"Ward Name", "Total Beds", "Occupied Beds"}, 0);
        table = new JTable(model);
        JScrollPane scrollPane = new JScrollPane(table);

        add(scrollPane, BorderLayout.CENTER);

        JPanel inputPanel = new JPanel(new GridLayout(2, 3));
        wardField = new JTextField();
        bedField = new JTextField();
        JButton addBtn = new JButton("Add / Update Ward");

        inputPanel.add(new JLabel("Ward Name:"));
        inputPanel.add(wardField);
        inputPanel.add(new JLabel());
        inputPanel.add(new JLabel("Total Beds:"));
        inputPanel.add(bedField);
        inputPanel.add(addBtn);

        add(inputPanel, BorderLayout.SOUTH);

        addBtn.addActionListener(e -> {
            String ward = wardField.getText().trim();
            int beds = Integer.parseInt(bedField.getText().trim());
            WardService.addOrUpdateWard(ward, beds);
            refreshTable();
        });

        refreshTable();
    }

    private void refreshTable() {
        model.setRowCount(0);
        Map<String, int[]> wards = WardService.getAllWards();
        for (var entry : wards.entrySet()) {
            model.addRow(new Object[]{
                    entry.getKey(),
                    entry.getValue()[0],
                    entry.getValue()[1]
            });
        }
    }
}
