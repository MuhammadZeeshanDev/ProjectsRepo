package storage;

import model.Patient;

import java.io.*;
import java.nio.file.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Saves and loads patient records from data/patients.txt.
 * The whole file is rewritten every time something changes, so the file
 * on disk is always up to date (no data is lost between runs).
 */
public class PatientStorage {

    private static final String FOLDER = "data";
    private static final String FILE_PATH = FOLDER + File.separator + "patients.txt";

    public PatientStorage() {
        FileUtil.ensureFileExists(FOLDER, FILE_PATH);
    }

    public List<Patient> loadAll() {
        List<Patient> list = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(FILE_PATH))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.isBlank()) {
                    list.add(Patient.fromFileLine(line));
                }
            }
        } catch (IOException e) {
            System.out.println("Could not read patients.txt: " + e.getMessage());
        }
        return list;
    }

    public void saveAll(List<Patient> patients) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(FILE_PATH))) {
            for (Patient p : patients) {
                writer.write(p.toFileLine());
                writer.newLine();
            }
        } catch (IOException e) {
            System.out.println("Could not save patients.txt: " + e.getMessage());
        }
    }
}
