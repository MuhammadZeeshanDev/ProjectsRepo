package util;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * The hospital's fixed list of wards and how many beds each one has.
 * Kept simple as constants rather than something the receptionist edits,
 * since a semester project does not need a "build your own hospital"
 * feature - just realistic, working bed tracking.
 */
public class Wards {

    public static final Map<String, Integer> BED_CAPACITY = new LinkedHashMap<>();

    static {
        BED_CAPACITY.put("General Ward", 10);
        BED_CAPACITY.put("ICU", 5);
        BED_CAPACITY.put("Surgical Ward", 8);
        BED_CAPACITY.put("Maternity Ward", 6);
        BED_CAPACITY.put("Pediatric Ward", 6);
    }

    public static String[] names() {
        return BED_CAPACITY.keySet().toArray(new String[0]);
    }

    public static int capacityOf(String wardName) {
        Integer capacity = BED_CAPACITY.get(wardName);
        return capacity == null ? 0 : capacity;
    }
}
