package storage;

import model.OPDVisit;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class OPDStorage {

    private static final String FOLDER = "data";
    private static final String FILE_PATH = FOLDER + File.separator + "opd_visits.txt";

    public OPDStorage() {
        FileUtil.ensureFileExists(FOLDER, FILE_PATH);
    }

    public List<OPDVisit> loadAll() {
        List<OPDVisit> list = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(FILE_PATH))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.isBlank()) {
                    list.add(OPDVisit.fromFileLine(line));
                }
            }
        } catch (IOException e) {
            System.out.println("Could not read opd_visits.txt: " + e.getMessage());
        }
        return list;
    }

    public void saveAll(List<OPDVisit> visits) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(FILE_PATH))) {
            for (OPDVisit v : visits) {
                writer.write(v.toFileLine());
                writer.newLine();
            }
        } catch (IOException e) {
            System.out.println("Could not save opd_visits.txt: " + e.getMessage());
        }
    }
}
