package service;

import model.Appointment;
import storage.AppointmentStorage;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Manages future appointments booked for already-registered patients.
 */
public class AppointmentService {

    private final AppointmentStorage storage;
    private final List<Appointment> appointments;

    public AppointmentService() {
        storage = new AppointmentStorage();
        appointments = storage.loadAll();
    }

    public List<Appointment> getAllAppointments() {
        return appointments;
    }

    /**
     * Books a new appointment. The date can be today or any day in the
     * future. Returns null if the doctor is already booked at that exact
     * date and time.
     */
    public Appointment bookAppointment(String patientId, String patientName, String doctorName,
                                        String department, LocalDate date, LocalTime time, String reason) {
        if (isDoctorBusy(doctorName, date, time)) {
            return null;
        }
        String newId = generateNextId();
        Appointment appointment = new Appointment(newId, patientId, patientName, doctorName,
                department, date, time, reason, "Scheduled");
        appointments.add(appointment);
        storage.saveAll(appointments);
        return appointment;
    }

    public void cancelAppointment(String appointmentId) {
        Appointment appointment = findById(appointmentId);
        if (appointment != null) {
            appointment.setStatus("Cancelled");
            storage.saveAll(appointments);
        }
    }

    public Appointment findById(String appointmentId) {
        for (Appointment a : appointments) {
            if (a.getAppointmentId().equals(appointmentId)) {
                return a;
            }
        }
        return null;
    }

    public List<Appointment> getAppointmentsByDate(LocalDate date) {
        List<Appointment> results = new ArrayList<>();
        for (Appointment a : appointments) {
            if (a.getAppointmentDate().equals(date)) {
                results.add(a);
            }
        }
        return results;
    }

    public List<Appointment> getUpcomingAppointments() {
        List<Appointment> results = new ArrayList<>();
        LocalDate today = LocalDate.now();
        for (Appointment a : appointments) {
            if (!a.getAppointmentDate().isBefore(today) && a.getStatus().equals("Scheduled")) {
                results.add(a);
            }
        }
        return results;
    }

    private boolean isDoctorBusy(String doctorName, LocalDate date, LocalTime time) {
        for (Appointment a : appointments) {
            boolean sameDoctor = a.getDoctorName().equalsIgnoreCase(doctorName);
            boolean sameSlot = a.getAppointmentDate().equals(date) && a.getAppointmentTime().equals(time);
            boolean stillActive = a.getStatus().equals("Scheduled");
            if (sameDoctor && sameSlot && stillActive) {
                return true;
            }
        }
        return false;
    }

    private String generateNextId() {
        int max = 0;
        for (Appointment a : appointments) {
            try {
                int number = Integer.parseInt(a.getAppointmentId().replace("A", ""));
                if (number > max) {
                    max = number;
                }
            } catch (NumberFormatException ignored) {
                // Skip any ID that does not follow the expected format.
            }
        }
        return String.format("A%04d", max + 1);
    }
}
