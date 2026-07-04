package service;

import model.WardAdmission;
import storage.WardStorage;
import util.Wards;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Manages ward beds and admissions. A patient is admitted to a ward
 * (usually shifted here from Emergency) and automatically given the
 * next free bed number in that ward. When they are discharged, the bed
 * becomes free again automatically - bed occupancy is always calculated
 * from the current list of active admissions rather than a separate
 * counter, so the two can never get out of sync.
 */
public class WardService {

    private final WardStorage storage;
    private final List<WardAdmission> admissions;

    public WardService() {
        storage = new WardStorage();
        admissions = storage.loadAll();
    }

    public List<WardAdmission> getAllAdmissions() {
        return admissions;
    }

    public List<WardAdmission> getActiveAdmissions() {
        List<WardAdmission> results = new ArrayList<>();
        for (WardAdmission a : admissions) {
            if (a.getStatus().equals("Admitted")) {
                results.add(a);
            }
        }
        return results;
    }

    public int occupiedBeds(String wardName) {
        int count = 0;
        for (WardAdmission a : admissions) {
            if (a.getWardName().equals(wardName) && a.getStatus().equals("Admitted")) {
                count++;
            }
        }
        return count;
    }

    public int availableBeds(String wardName) {
        return Wards.capacityOf(wardName) - occupiedBeds(wardName);
    }

    /**
     * Admits a patient into the given ward, automatically picking the
     * first free bed number. Returns null if the ward is completely full.
     */
    public WardAdmission admitPatient(String patientId, String patientName, String wardName,
                                       String doctorName, String notes) {
        Integer freeBed = findFreeBed(wardName);
        if (freeBed == null) {
            return null; // ward is full
        }
        String newId = generateNextId();
        WardAdmission admission = new WardAdmission(newId, patientId, patientName, wardName,
                freeBed, doctorName, LocalDate.now(), notes, "Admitted");
        admissions.add(admission);
        storage.saveAll(admissions);
        return admission;
    }

    public void dischargePatient(String admissionId) {
        for (WardAdmission a : admissions) {
            if (a.getAdmissionId().equals(admissionId)) {
                a.setStatus("Discharged");
                storage.saveAll(admissions);
                return;
            }
        }
    }

    private Integer findFreeBed(String wardName) {
        int capacity = Wards.capacityOf(wardName);
        Set<Integer> takenBeds = new HashSet<>();
        for (WardAdmission a : admissions) {
            if (a.getWardName().equals(wardName) && a.getStatus().equals("Admitted")) {
                takenBeds.add(a.getBedNumber());
            }
        }
        for (int bed = 1; bed <= capacity; bed++) {
            if (!takenBeds.contains(bed)) {
                return bed;
            }
        }
        return null;
    }

    private String generateNextId() {
        int max = 0;
        for (WardAdmission a : admissions) {
            try {
                int number = Integer.parseInt(a.getAdmissionId().replace("W", ""));
                if (number > max) {
                    max = number;
                }
            } catch (NumberFormatException ignored) {
                // Skip any ID that does not follow the expected format.
            }
        }
        return String.format("W%04d", max + 1);
    }
}
