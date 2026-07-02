package service;

import model.Patient;
import java.util.ArrayList;
import java.util.List;

public class PatientService {
    private final List<Patient> patients = new ArrayList<>();

    public void addPatient(Patient patient) {
        patients.add(patient);
    }

    public void dischargePatient(String id) {
        patients.removeIf(p -> p.getId().equals(id));
    }

    public List<Patient> getAllPatients() {
        return new ArrayList<>(patients);
    }
}
