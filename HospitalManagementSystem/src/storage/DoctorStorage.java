package storage;

import model.Doctor;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class DoctorStorage {

    private static final String FOLDER = "data";
    private static final String FILE_PATH = FOLDER + File.separator + "doctors.txt";

    public DoctorStorage() {
        FileUtil.ensureFileExists(FOLDER, FILE_PATH);
    }

    public List<Doctor> loadAll() {
        List<Doctor> list = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(FILE_PATH))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.isBlank()) {
                    list.add(Doctor.fromFileLine(line));
                }
            }
        } catch (IOException e) {
            System.out.println("Could not read doctors.txt: " + e.getMessage());
        }
        return list;
    }

    public void saveAll(List<Doctor> doctors) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(FILE_PATH))) {
            for (Doctor d : doctors) {
                writer.write(d.toFileLine());
                writer.newLine();
            }
        } catch (IOException e) {
            System.out.println("Could not save doctors.txt: " + e.getMessage());
        }
    }
}
