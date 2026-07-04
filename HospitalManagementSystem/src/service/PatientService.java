package service;

import model.Patient;
import storage.PatientStorage;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/**
 * Manages the master patient list. OPD and Emergency both register
 * patients through this service, and Appointments searches through it
 * to find an existing patient - so a patient's details only ever need
 * to be typed in once.
 */
public class PatientService {

    private final PatientStorage storage;
    private final List<Patient> patients;

    public PatientService() {
        storage = new PatientStorage();
        patients = storage.loadAll();
    }

    public List<Patient> getAllPatients() {
        return patients;
    }

    public Patient findById(String patientId) {
        for (Patient p : patients) {
            if (p.getPatientId().equals(patientId)) {
                return p;
            }
        }
        return null;
    }

    /** Looks for an existing patient with this exact phone number. */
    public Patient findByPhone(String phone) {
        for (Patient p : patients) {
            if (p.getPhone().equals(phone)) {
                return p;
            }
        }
        return null;
    }

    /**
     * Used by the OPD and Emergency intake forms: if a patient with this
     * phone number is already registered, their existing record is reused
     * (so the same person is not registered twice); otherwise a brand new
     * patient record is created.
     */
    public Patient registerOrFindPatient(String name, int age, String gender, String phone, String address) {
        Patient existing = findByPhone(phone);
        if (existing != null) {
            return existing;
        }
        String newId = generateNextId();
        Patient patient = new Patient(newId, name, age, gender, phone, address, LocalDate.now());
        patients.add(patient);
        storage.saveAll(patients);
        return patient;
    }

    /** Returns every patient whose name, ID, or phone number contains the given text. */
    public List<Patient> search(String keyword) {
        List<Patient> results = new ArrayList<>();
        String lowerKeyword = keyword.toLowerCase();
        for (Patient p : patients) {
            if (p.getName().toLowerCase().contains(lowerKeyword)
                    || p.getPatientId().toLowerCase().contains(lowerKeyword)
                    || p.getPhone().toLowerCase().contains(lowerKeyword)) {
                results.add(p);
            }
        }
        return results;
    }

    private String generateNextId() {
        int max = 0;
        for (Patient p : patients) {
            try {
                int number = Integer.parseInt(p.getPatientId().replace("P", ""));
                if (number > max) {
                    max = number;
                }
            } catch (NumberFormatException ignored) {
                // Skip any ID that does not follow the expected format.
            }
        }
        return String.format("P%04d", max + 1);
    }
}
