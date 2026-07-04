package ui;

import model.Doctor;

/**
 * Wraps a Doctor so combo boxes can display "Name - Department" while
 * still giving easy access to the full Doctor object underneath. Shared
 * by every panel that needs to pick a doctor (OPD, Emergency, Appointments).
 */
class DoctorOption {
    final Doctor doctor;

    DoctorOption(Doctor doctor) {
        this.doctor = doctor;
    }

    @Override
    public String toString() {
        return doctor.getName() + " - " + doctor.getDepartment();
    }
}
