package service;

import model.OPDVisit;
import storage.OPDStorage;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/**
 * Manages OPD (Out-Patient / general check-up) visits.
 */
public class OPDService {

    private final OPDStorage storage;
    private final List<OPDVisit> visits;

    public OPDService() {
        storage = new OPDStorage();
        visits = storage.loadAll();
    }

    public List<OPDVisit> getAllVisits() {
        return visits;
    }

    public List<OPDVisit> getActiveVisits() {
        List<OPDVisit> results = new ArrayList<>();
        for (OPDVisit v : visits) {
            if (v.getStatus().equals("Under Treatment")) {
                results.add(v);
            }
        }
        return results;
    }

    public OPDVisit findById(String opdId) {
        for (OPDVisit v : visits) {
            if (v.getOpdId().equals(opdId)) {
                return v;
            }
        }
        return null;
    }

    public OPDVisit registerVisit(String patientId, String patientName, int age, String gender,
                                   String doctorName, String department, String symptoms) {
        String newId = generateNextId();
        OPDVisit visit = new OPDVisit(newId, patientId, patientName, age, gender,
                doctorName, department, symptoms, LocalDate.now(), "Under Treatment");
        visits.add(visit);
        storage.saveAll(visits);
        return visit;
    }

    public void updateStatus(String opdId, String newStatus) {
        OPDVisit visit = findById(opdId);
        if (visit != null) {
            visit.setStatus(newStatus);
            storage.saveAll(visits);
        }
    }

    private String generateNextId() {
        int max = 0;
        for (OPDVisit v : visits) {
            try {
                int number = Integer.parseInt(v.getOpdId().replace("O", ""));
                if (number > max) {
                    max = number;
                }
            } catch (NumberFormatException ignored) {
                // Skip any ID that does not follow the expected format.
            }
        }
        return String.format("O%04d", max + 1);
    }
}
