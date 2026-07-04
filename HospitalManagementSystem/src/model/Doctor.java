package model;

/**
 * A doctor's details. This is the master list that every other panel
 * (OPD, Emergency, Appointments) picks a doctor from, instead of the
 * receptionist typing a doctor's name freely each time.
 */
public class Doctor {

    private String doctorId;
    private String name;
    private String department;
    private String phone;
    private String status; // "Available" or "On Leave"

    public Doctor(String doctorId, String name, String department, String phone, String status) {
        this.doctorId = doctorId;
        this.name = name;
        this.department = department;
        this.phone = phone;
        this.status = status;
    }

    public String getDoctorId() {
        return doctorId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDepartment() {
        return department;
    }

    public void setDepartment(String department) {
        this.department = department;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String toFileLine() {
        return doctorId + "|" + name + "|" + department + "|" + phone + "|" + status;
    }

    public static Doctor fromFileLine(String line) {
        String[] p = line.split("\\|", -1);
        return new Doctor(p[0], p[1], p[2], p[3], p[4]);
    }
}
