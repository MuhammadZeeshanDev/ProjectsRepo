import ui.LoginScreen;

import javax.swing.*;

/**
 * Entry point of the Hospital Management System.
 * Applies a nicer look-and-feel (Nimbus, built into Java) and then
 * opens the login screen.
 */
public class Main {
    public static void main(String[] args) {
        try {
            for (UIManager.LookAndFeelInfo info : UIManager.getInstalledLookAndFeels()) {
                if ("Nimbus".equals(info.getName())) {
                    UIManager.setLookAndFeel(info.getClassName());
                    break;
                }
            }
        } catch (Exception e) {
            // If Nimbus isn't available for some reason, the app still runs
            // fine with the default Java look and feel.
        }

        SwingUtilities.invokeLater(() -> new LoginScreen().setVisible(true));
    }
}
