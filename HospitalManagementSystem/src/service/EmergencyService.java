package service;

import model.EmergencyCase;
import storage.EmergencyStorage;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Manages Emergency cases - patients in a serious condition. From here a
 * case can later be shifted into a ward bed or discharged directly.
 */
public class EmergencyService {

    private final EmergencyStorage storage;
    private final List<EmergencyCase> cases;

    public EmergencyService() {
        storage = new EmergencyStorage();
        cases = storage.loadAll();
    }

    public List<EmergencyCase> getAllCases() {
        return cases;
    }

    public List<EmergencyCase> getActiveCases() {
        List<EmergencyCase> results = new ArrayList<>();
        for (EmergencyCase c : cases) {
            if (c.getStatus().equals("In Emergency")) {
                results.add(c);
            }
        }
        return results;
    }

    public EmergencyCase findById(String emergencyId) {
        for (EmergencyCase c : cases) {
            if (c.getEmergencyId().equals(emergencyId)) {
                return c;
            }
        }
        return null;
    }

    public EmergencyCase registerCase(String patientId, String patientName, int age, String gender,
                                       String condition, String doctorName, String department) {
        String newId = generateNextId();
        EmergencyCase emergencyCase = new EmergencyCase(newId, patientId, patientName, age, gender,
                condition, doctorName, department, LocalDate.now(), LocalTime.now().withSecond(0).withNano(0),
                "In Emergency");
        cases.add(emergencyCase);
        storage.saveAll(cases);
        return emergencyCase;
    }

    public void updateStatus(String emergencyId, String newStatus) {
        EmergencyCase emergencyCase = findById(emergencyId);
        if (emergencyCase != null) {
            emergencyCase.setStatus(newStatus);
            storage.saveAll(cases);
        }
    }

    private String generateNextId() {
        int max = 0;
        for (EmergencyCase c : cases) {
            try {
                int number = Integer.parseInt(c.getEmergencyId().replace("E", ""));
                if (number > max) {
                    max = number;
                }
            } catch (NumberFormatException ignored) {
                // Skip any ID that does not follow the expected format.
            }
        }
        return String.format("E%04d", max + 1);
    }
}
