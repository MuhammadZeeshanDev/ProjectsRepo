package ui;

import model.WardAdmission;
import service.WardService;
import util.Theme;
import util.Wards;

import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.awt.event.ComponentAdapter;
import java.awt.event.ComponentEvent;
import java.util.List;

/**
 * Wards desk: shows how many beds each ward has, how many are currently
 * occupied, and the full details of every admitted patient. Patients
 * normally arrive here after being shifted from the Emergency tab.
 */
public class WardPanel extends JPanel {

    private final WardService wardService;

    private DefaultTableModel summaryTableModel;
    private DefaultTableModel admissionsTableModel;
    private JTable admissionsTable;

    public WardPanel(WardService wardService) {
        this.wardService = wardService;

        setLayout(new BorderLayout(16, 16));
        setBorder(BorderFactory.createEmptyBorder(16, 16, 16, 16));
        setBackground(Theme.BACKGROUND);

        add(buildSummaryPanel(), BorderLayout.NORTH);
        add(buildAdmissionsPanel(), BorderLayout.CENTER);

        refreshAll();

        addComponentListener(new ComponentAdapter() {
            @Override
            public void componentShown(ComponentEvent e) {
                refreshAll();
            }
        });
    }

    private JPanel buildSummaryPanel() {
        JPanel outer = new JPanel(new BorderLayout(0, 8));
        outer.setBackground(Theme.BACKGROUND);

        JLabel heading = new JLabel("Ward Bed Occupancy");
        heading.setFont(Theme.FONT_HEADING);
        heading.setForeground(Theme.TEXT_DARK);

        summaryTableModel = new DefaultTableModel(
                new String[]{"Ward", "Total Beds", "Occupied", "Available"}, 0) {
            @Override
            public boolean isCellEditable(int row, int column) {
                return false;
            }
        };
        JTable summaryTable = new JTable(summaryTableModel);
        summaryTable.setFont(Theme.FONT_NORMAL);
        summaryTable.setRowHeight(26);
        summaryTable.getTableHeader().setFont(Theme.FONT_LABEL);
        summaryTable.setPreferredScrollableViewportSize(new Dimension(0, 140));

        JScrollPane scrollPane = new JScrollPane(summaryTable);
        scrollPane.setBorder(BorderFactory.createLineBorder(Theme.BORDER));

        outer.add(heading, BorderLayout.NORTH);
        outer.add(scrollPane, BorderLayout.CENTER);
        return outer;
    }

    private JPanel buildAdmissionsPanel() {
        JPanel outer = new JPanel(new BorderLayout(0, 8));
        outer.setBackground(Theme.BACKGROUND);

        JLabel heading = new JLabel("Admitted Patients");
        heading.setFont(Theme.FONT_HEADING);
        heading.setForeground(Theme.TEXT_DARK);

        admissionsTableModel = new DefaultTableModel(
                new String[]{"Admission ID", "Patient", "Ward", "Bed No.", "Doctor",
                        "Admission Date", "Notes", "Status"}, 0) {
            @Override
            public boolean isCellEditable(int row, int column) {
                return false;
            }
        };
        admissionsTable = new JTable(admissionsTableModel);
        admissionsTable.setFont(Theme.FONT_NORMAL);
        admissionsTable.setRowHeight(26);
        admissionsTable.getTableHeader().setFont(Theme.FONT_LABEL);
        admissionsTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);

        JScrollPane scrollPane = new JScrollPane(admissionsTable);
        scrollPane.setBorder(BorderFactory.createLineBorder(Theme.BORDER));

        JButton dischargeButton = new JButton("Discharge Selected Patient");
        Theme.styleDangerButton(dischargeButton);
        dischargeButton.addActionListener(e -> dischargeSelected());

        JButton showAllButton = new JButton("Show All (incl. Discharged)");
        Theme.styleSecondaryButton(showAllButton);
        showAllButton.addActionListener(e -> refreshAdmissionsTable(wardService.getAllAdmissions()));

        JButton showActiveButton = new JButton("Show Currently Admitted");
        Theme.stylePrimaryButton(showActiveButton);
        showActiveButton.addActionListener(e -> refreshAdmissionsTable(wardService.getActiveAdmissions()));

        JPanel bottomBar = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 8));
        bottomBar.setBackground(Theme.BACKGROUND);
        bottomBar.add(showActiveButton);
        bottomBar.add(showAllButton);
        bottomBar.add(dischargeButton);

        outer.add(heading, BorderLayout.NORTH);
        outer.add(scrollPane, BorderLayout.CENTER);
        outer.add(bottomBar, BorderLayout.SOUTH);
        return outer;
    }

    private void dischargeSelected() {
        int row = admissionsTable.getSelectedRow();
        if (row == -1) {
            JOptionPane.showMessageDialog(this, "Select an admitted patient from the table first.",
                    "No patient selected", JOptionPane.WARNING_MESSAGE);
            return;
        }
        String admissionId = (String) admissionsTableModel.getValueAt(row, 0);
        String status = (String) admissionsTableModel.getValueAt(row, 7);
        if (!status.equals("Admitted")) {
            JOptionPane.showMessageDialog(this, "This patient has already been discharged.",
                    "Cannot update", JOptionPane.WARNING_MESSAGE);
            return;
        }
        int choice = JOptionPane.showConfirmDialog(this, "Discharge this patient and free up their bed?",
                "Confirm Discharge", JOptionPane.YES_NO_OPTION);
        if (choice == JOptionPane.YES_OPTION) {
            wardService.dischargePatient(admissionId);
            refreshAll();
        }
    }

    private void refreshAll() {
        refreshSummaryTable();
        refreshAdmissionsTable(wardService.getActiveAdmissions());
    }

    private void refreshSummaryTable() {
        summaryTableModel.setRowCount(0);
        for (String wardName : Wards.names()) {
            int total = Wards.capacityOf(wardName);
            int occupied = wardService.occupiedBeds(wardName);
            int available = total - occupied;
            summaryTableModel.addRow(new Object[]{wardName, total, occupied, available});
        }
    }

    private void refreshAdmissionsTable(List<WardAdmission> admissions) {
        admissionsTableModel.setRowCount(0);
        for (WardAdmission a : admissions) {
            admissionsTableModel.addRow(new Object[]{
                    a.getAdmissionId(), a.getPatientName(), a.getWardName(), a.getBedNumber(),
                    a.getDoctorName(), a.getAdmissionDate(), a.getNotes(), a.getStatus()
            });
        }
    }
}
