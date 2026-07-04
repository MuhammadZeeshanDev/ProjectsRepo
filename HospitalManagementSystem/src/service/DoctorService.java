package service;

import model.Doctor;
import storage.DoctorStorage;

import java.util.List;

/**
 * Manages the doctors master list used across OPD, Emergency, Wards,
 * and Appointments.
 */
public class DoctorService {

    private final DoctorStorage storage;
    private final List<Doctor> doctors;

    public DoctorService() {
        storage = new DoctorStorage();
        doctors = storage.loadAll();

        // The very first time the app runs, there will be no doctors yet.
        // A handful of sample doctors are added automatically so the app
        // is usable (and easy to demo) right away.
        if (doctors.isEmpty()) {
            doctors.add(new Doctor("D001", "Dr. Ahmed Khan", "Cardiology", "0300-1112233", "Available"));
            doctors.add(new Doctor("D002", "Dr. Sara Malik", "General Medicine", "0300-2223344", "Available"));
            doctors.add(new Doctor("D003", "Dr. Bilal Hussain", "Emergency Medicine", "0300-3334455", "Available"));
            doctors.add(new Doctor("D004", "Dr. Ayesha Raza", "Pediatrics", "0300-4445566", "Available"));
            doctors.add(new Doctor("D005", "Dr. Omar Farooq", "Orthopedics", "0300-5556677", "Available"));
            storage.saveAll(doctors);
        }
    }

    public List<Doctor> getAllDoctors() {
        return doctors;
    }

    public Doctor findById(String doctorId) {
        for (Doctor d : doctors) {
            if (d.getDoctorId().equals(doctorId)) {
                return d;
            }
        }
        return null;
    }

    public Doctor addDoctor(String name, String department, String phone) {
        String newId = generateNextId();
        Doctor doctor = new Doctor(newId, name, department, phone, "Available");
        doctors.add(doctor);
        storage.saveAll(doctors);
        return doctor;
    }

    public void updateDoctor(String doctorId, String name, String department, String phone, String status) {
        Doctor doctor = findById(doctorId);
        if (doctor != null) {
            doctor.setName(name);
            doctor.setDepartment(department);
            doctor.setPhone(phone);
            doctor.setStatus(status);
            storage.saveAll(doctors);
        }
    }

    public boolean deleteDoctor(String doctorId) {
        Doctor doctor = findById(doctorId);
        if (doctor != null) {
            doctors.remove(doctor);
            storage.saveAll(doctors);
            return true;
        }
        return false;
    }

    private String generateNextId() {
        int max = 0;
        for (Doctor d : doctors) {
            try {
                int number = Integer.parseInt(d.getDoctorId().replace("D", ""));
                if (number > max) {
                    max = number;
                }
            } catch (NumberFormatException ignored) {
                // Skip any ID that does not follow the expected format.
            }
        }
        return String.format("D%03d", max + 1);
    }
}
