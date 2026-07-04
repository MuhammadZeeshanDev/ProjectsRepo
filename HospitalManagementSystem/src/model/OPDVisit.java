package model;

import java.time.LocalDate;

/**
 * One OPD (Out-Patient Department) visit - a patient who walked in for a
 * routine/general check-up, as opposed to an emergency case.
 */
public class OPDVisit {

    private String opdId;
    private String patientId;
    private String patientName;
    private int age;
    private String gender;
    private String doctorName;
    private String department;
    private String symptoms;
    private LocalDate visitDate;
    private String status; // "Under Treatment", "Discharged", "Referred to Emergency"

    public OPDVisit(String opdId, String patientId, String patientName, int age, String gender,
                     String doctorName, String department, String symptoms,
                     LocalDate visitDate, String status) {
        this.opdId = opdId;
        this.patientId = patientId;
        this.patientName = patientName;
        this.age = age;
        this.gender = gender;
        this.doctorName = doctorName;
        this.department = department;
        this.symptoms = symptoms;
        this.visitDate = visitDate;
        this.status = status;
    }

    public String getOpdId() {
        return opdId;
    }

    public String getPatientId() {
        return patientId;
    }

    public String getPatientName() {
        return patientName;
    }

    public int getAge() {
        return age;
    }

    public String getGender() {
        return gender;
    }

    public String getDoctorName() {
        return doctorName;
    }

    public String getDepartment() {
        return department;
    }

    public String getSymptoms() {
        return symptoms;
    }

    public LocalDate getVisitDate() {
        return visitDate;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String toFileLine() {
        return opdId + "|" + patientId + "|" + patientName + "|" + age + "|" + gender + "|"
                + doctorName + "|" + department + "|" + symptoms + "|" + visitDate + "|" + status;
    }

    public static OPDVisit fromFileLine(String line) {
        String[] p = line.split("\\|", -1);
        return new OPDVisit(p[0], p[1], p[2], Integer.parseInt(p[3]), p[4], p[5], p[6], p[7],
                LocalDate.parse(p[8]), p[9]);
    }
}
