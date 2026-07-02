import db.DatabaseManager;
import ui.LoginScreen;

import javax.swing.*;
import java.awt.*;

public class Main {
    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            Font font = new Font("Segoe UI", Font.PLAIN, 14);
            UIManager.put("Label.font", font);
            UIManager.put("Button.font", font);
            UIManager.put("TextField.font", font);
            UIManager.put("ComboBox.font", font);
            UIManager.put("PasswordField.font", font);
            UIManager.put("CheckBox.font", font);
            UIManager.put("Table.font", font);
            UIManager.put("Table.rowHeight", 22);
        } catch (Exception ignored) {}

        DatabaseManager.initialize();
        SwingUtilities.invokeLater(() -> new LoginScreen().setVisible(true));
    }
}
