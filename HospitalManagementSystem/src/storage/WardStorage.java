package storage;

import model.WardAdmission;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class WardStorage {

    private static final String FOLDER = "data";
    private static final String FILE_PATH = FOLDER + File.separator + "ward_admissions.txt";

    public WardStorage() {
        FileUtil.ensureFileExists(FOLDER, FILE_PATH);
    }

    public List<WardAdmission> loadAll() {
        List<WardAdmission> list = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(FILE_PATH))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.isBlank()) {
                    list.add(WardAdmission.fromFileLine(line));
                }
            }
        } catch (IOException e) {
            System.out.println("Could not read ward_admissions.txt: " + e.getMessage());
        }
        return list;
    }

    public void saveAll(List<WardAdmission> admissions) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(FILE_PATH))) {
            for (WardAdmission a : admissions) {
                writer.write(a.toFileLine());
                writer.newLine();
            }
        } catch (IOException e) {
            System.out.println("Could not save ward_admissions.txt: " + e.getMessage());
        }
    }
}
