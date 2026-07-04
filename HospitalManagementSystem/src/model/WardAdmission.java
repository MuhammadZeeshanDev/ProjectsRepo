package model;

import java.time.LocalDate;

/**
 * One ward admission - a patient occupying a specific bed in a specific
 * ward, usually created when a receptionist shifts a patient out of
 * Emergency.
 */
public class WardAdmission {

    private String admissionId;
    private String patientId;
    private String patientName;
    private String wardName;
    private int bedNumber;
    private String doctorName;
    private LocalDate admissionDate;
    private String notes;
    private String status; // "Admitted" or "Discharged"

    public WardAdmission(String admissionId, String patientId, String patientName, String wardName,
                          int bedNumber, String doctorName, LocalDate admissionDate,
                          String notes, String status) {
        this.admissionId = admissionId;
        this.patientId = patientId;
        this.patientName = patientName;
        this.wardName = wardName;
        this.bedNumber = bedNumber;
        this.doctorName = doctorName;
        this.admissionDate = admissionDate;
        this.notes = notes;
        this.status = status;
    }

    public String getAdmissionId() {
        return admissionId;
    }

    public String getPatientId() {
        return patientId;
    }

    public String getPatientName() {
        return patientName;
    }

    public String getWardName() {
        return wardName;
    }

    public int getBedNumber() {
        return bedNumber;
    }

    public String getDoctorName() {
        return doctorName;
    }

    public LocalDate getAdmissionDate() {
        return admissionDate;
    }

    public String getNotes() {
        return notes;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String toFileLine() {
        return admissionId + "|" + patientId + "|" + patientName + "|" + wardName + "|" + bedNumber + "|"
                + doctorName + "|" + admissionDate + "|" + notes + "|" + status;
    }

    public static WardAdmission fromFileLine(String line) {
        String[] p = line.split("\\|", -1);
        return new WardAdmission(p[0], p[1], p[2], p[3], Integer.parseInt(p[4]), p[5],
                LocalDate.parse(p[6]), p[7], p[8]);
    }
}
