package storage;

import model.Appointment;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class AppointmentStorage {

    private static final String FOLDER = "data";
    private static final String FILE_PATH = FOLDER + File.separator + "appointments.txt";

    public AppointmentStorage() {
        FileUtil.ensureFileExists(FOLDER, FILE_PATH);
    }

    public List<Appointment> loadAll() {
        List<Appointment> list = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(FILE_PATH))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.isBlank()) {
                    list.add(Appointment.fromFileLine(line));
                }
            }
        } catch (IOException e) {
            System.out.println("Could not read appointments.txt: " + e.getMessage());
        }
        return list;
    }

    public void saveAll(List<Appointment> appointments) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(FILE_PATH))) {
            for (Appointment a : appointments) {
                writer.write(a.toFileLine());
                writer.newLine();
            }
        } catch (IOException e) {
            System.out.println("Could not save appointments.txt: " + e.getMessage());
        }
    }
}
