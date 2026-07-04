package model;

import java.time.LocalDate;
import java.time.LocalTime;

/**
 * One Emergency case - a patient in a serious condition. From here the
 * receptionist can shift the patient into a ward (bed assignment) once
 * a doctor decides they need to be admitted, or discharge them directly.
 */
public class EmergencyCase {

    private String emergencyId;
    private String patientId;
    private String patientName;
    private int age;
    private String gender;
    private String condition; // "Critical", "Serious", "Stable"
    private String doctorName;
    private String department;
    private LocalDate arrivalDate;
    private LocalTime arrivalTime;
    private String status; // "In Emergency", "Shifted to Ward", "Discharged"

    public EmergencyCase(String emergencyId, String patientId, String patientName, int age, String gender,
                          String condition, String doctorName, String department,
                          LocalDate arrivalDate, LocalTime arrivalTime, String status) {
        this.emergencyId = emergencyId;
        this.patientId = patientId;
        this.patientName = patientName;
        this.age = age;
        this.gender = gender;
        this.condition = condition;
        this.doctorName = doctorName;
        this.department = department;
        this.arrivalDate = arrivalDate;
        this.arrivalTime = arrivalTime;
        this.status = status;
    }

    public String getEmergencyId() {
        return emergencyId;
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

    public String getCondition() {
        return condition;
    }

    public String getDoctorName() {
        return doctorName;
    }

    public String getDepartment() {
        return department;
    }

    public LocalDate getArrivalDate() {
        return arrivalDate;
    }

    public LocalTime getArrivalTime() {
        return arrivalTime;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String toFileLine() {
        return emergencyId + "|" + patientId + "|" + patientName + "|" + age + "|" + gender + "|"
                + condition + "|" + doctorName + "|" + department + "|" + arrivalDate + "|"
                + arrivalTime + "|" + status;
    }

    public static EmergencyCase fromFileLine(String line) {
        String[] p = line.split("\\|", -1);
        return new EmergencyCase(p[0], p[1], p[2], Integer.parseInt(p[3]), p[4], p[5], p[6], p[7],
                LocalDate.parse(p[8]), LocalTime.parse(p[9]), p[10]);
    }
}
