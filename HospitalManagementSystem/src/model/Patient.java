package model;

import java.time.LocalDate;

/**
 * A patient's core details. Every patient is registered only once
 * (either at the OPD desk or the Emergency desk, whichever they visit
 * first) and the same record is then reused everywhere else in the
 * system - Emergency, Wards, and Appointments all refer back to this
 * same patient by patientId instead of asking for the details again.
 */
public class Patient {

    private String patientId;
    private String name;
    private int age;
    private String gender;
    private String phone;
    private String address;
    private LocalDate registrationDate;

    public Patient(String patientId, String name, int age, String gender,
                    String phone, String address, LocalDate registrationDate) {
        this.patientId = patientId;
        this.name = name;
        this.age = age;
        this.gender = gender;
        this.phone = phone;
        this.address = address;
        this.registrationDate = registrationDate;
    }

    public String getPatientId() {
        return patientId;
    }

    public String getName() {
        return name;
    }

    public int getAge() {
        return age;
    }

    public String getGender() {
        return gender;
    }

    public String getPhone() {
        return phone;
    }

    public String getAddress() {
        return address;
    }

    public LocalDate getRegistrationDate() {
        return registrationDate;
    }

    public String toFileLine() {
        return patientId + "|" + name + "|" + age + "|" + gender + "|"
                + phone + "|" + address + "|" + registrationDate;
    }

    public static Patient fromFileLine(String line) {
        String[] p = line.split("\\|", -1);
        return new Patient(p[0], p[1], Integer.parseInt(p[2]), p[3], p[4], p[5], LocalDate.parse(p[6]));
    }
}
