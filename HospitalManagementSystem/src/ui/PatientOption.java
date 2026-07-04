package ui;

import model.Patient;

/**
 * Wraps a Patient so combo boxes can display "ID - Name" while still
 * giving easy access to the full Patient object underneath. Shared by
 * the Appointments panel.
 */
class PatientOption {
    final Patient patient;

    PatientOption(Patient patient) {
        this.patient = patient;
    }

    @Override
    public String toString() {
        return patient.getPatientId() + " - " + patient.getName();
    }
}
