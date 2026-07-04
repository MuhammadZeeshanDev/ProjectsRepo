package util;

import javax.swing.*;
import java.awt.*;

/**
 * Holds the colors and fonts used across the application so every
 * screen looks consistent, plus a few helper methods for styling
 * buttons the same way everywhere.
 */
public class Theme {

    public static final Color PRIMARY = new Color(30, 96, 145);
    public static final Color PRIMARY_DARK = new Color(20, 70, 110);
    public static final Color ACCENT = new Color(56, 176, 137);
    public static final Color DANGER = new Color(196, 68, 68);
    public static final Color WARNING = new Color(214, 149, 43);
    public static final Color BACKGROUND = new Color(244, 247, 250);
    public static final Color PANEL_BACKGROUND = Color.WHITE;
    public static final Color BORDER = new Color(214, 222, 230);
    public static final Color TEXT_DARK = new Color(35, 45, 55);
    public static final Color TEXT_MUTED = new Color(110, 122, 134);

    public static final Font FONT_TITLE = new Font("Segoe UI", Font.BOLD, 22);
    public static final Font FONT_HEADING = new Font("Segoe UI", Font.BOLD, 15);
    public static final Font FONT_NORMAL = new Font("Segoe UI", Font.PLAIN, 13);
    public static final Font FONT_LABEL = new Font("Segoe UI", Font.BOLD, 13);

    public static void stylePrimaryButton(JButton button) {
        style(button, PRIMARY, Color.WHITE);
    }

    public static void styleAccentButton(JButton button) {
        style(button, ACCENT, Color.WHITE);
    }

    public static void styleDangerButton(JButton button) {
        style(button, DANGER, Color.WHITE);
    }

    public static void styleWarningButton(JButton button) {
        style(button, WARNING, Color.WHITE);
    }

    public static void styleSecondaryButton(JButton button) {
        button.setFont(FONT_LABEL);
        button.setBackground(Color.WHITE);
        button.setForeground(PRIMARY);
        button.setFocusPainted(false);
        button.setCursor(new Cursor(Cursor.HAND_CURSOR));
        button.setBorder(BorderFactory.createLineBorder(PRIMARY, 1, true));
    }

    private static void style(JButton button, Color background, Color foreground) {
        button.setFont(FONT_LABEL);
        button.setBackground(background);
        button.setForeground(foreground);
        button.setFocusPainted(false);
        button.setCursor(new Cursor(Cursor.HAND_CURSOR));
        button.setBorder(BorderFactory.createEmptyBorder(10, 16, 10, 16));
    }
}
