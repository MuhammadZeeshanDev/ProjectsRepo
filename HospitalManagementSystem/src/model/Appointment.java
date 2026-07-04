package model;

import java.time.LocalDate;
import java.time.LocalTime;

/**
 * A future appointment booked for an already-registered patient with a
 * doctor picked from the Doctors master list.
 */
public class Appointment {

    private String appointmentId;
    private String patientId;
    private String patientName;
    private String doctorName;
    private String department;
    private LocalDate appointmentDate;
    private LocalTime appointmentTime;
    private String reason;
    private String status; // "Scheduled" or "Cancelled"

    public Appointment(String appointmentId, String patientId, String patientName,
                        String doctorName, String department, LocalDate appointmentDate,
                        LocalTime appointmentTime, String reason, String status) {
        this.appointmentId = appointmentId;
        this.patientId = patientId;
        this.patientName = patientName;
        this.doctorName = doctorName;
        this.department = department;
        this.appointmentDate = appointmentDate;
        this.appointmentTime = appointmentTime;
        this.reason = reason;
        this.status = status;
    }

    public String getAppointmentId() {
        return appointmentId;
    }

    public String getPatientId() {
        return patientId;
    }

    public String getPatientName() {
        return patientName;
    }

    public String getDoctorName() {
        return doctorName;
    }

    public String getDepartment() {
        return department;
    }

    public LocalDate getAppointmentDate() {
        return appointmentDate;
    }

    public LocalTime getAppointmentTime() {
        return appointmentTime;
    }

    public String getReason() {
        return reason;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String toFileLine() {
        return appointmentId + "|" + patientId + "|" + patientName + "|" + doctorName + "|"
                + department + "|" + appointmentDate + "|" + appointmentTime + "|"
                + reason + "|" + status;
    }

    public static Appointment fromFileLine(String line) {
        String[] p = line.split("\\|", -1);
        return new Appointment(p[0], p[1], p[2], p[3], p[4], LocalDate.parse(p[5]),
                LocalTime.parse(p[6]), p[7], p[8]);
    }
}
