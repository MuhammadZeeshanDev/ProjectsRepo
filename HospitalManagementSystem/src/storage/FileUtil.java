package storage;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

/**
 * Tiny shared helper used by every *Storage class so each one does not
 * have to repeat the same "create the data folder and file if missing"
 * code.
 */
class FileUtil {

    static void ensureFileExists(String folder, String filePath) {
        try {
            Files.createDirectories(Paths.get(folder));
            File file = new File(filePath);
            if (!file.exists()) {
                file.createNewFile();
            }
        } catch (IOException e) {
            System.out.println("Could not prepare " + filePath + ": " + e.getMessage());
        }
    }
}
