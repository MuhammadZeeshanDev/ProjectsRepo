package storage;

import model.EmergencyCase;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class EmergencyStorage {

    private static final String FOLDER = "data";
    private static final String FILE_PATH = FOLDER + File.separator + "emergency_cases.txt";

    public EmergencyStorage() {
        FileUtil.ensureFileExists(FOLDER, FILE_PATH);
    }

    public List<EmergencyCase> loadAll() {
        List<EmergencyCase> list = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(FILE_PATH))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.isBlank()) {
                    list.add(EmergencyCase.fromFileLine(line));
                }
            }
        } catch (IOException e) {
            System.out.println("Could not read emergency_cases.txt: " + e.getMessage());
        }
        return list;
    }

    public void saveAll(List<EmergencyCase> cases) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(FILE_PATH))) {
            for (EmergencyCase c : cases) {
                writer.write(c.toFileLine());
                writer.newLine();
            }
        } catch (IOException e) {
            System.out.println("Could not save emergency_cases.txt: " + e.getMessage());
        }
    }
}
