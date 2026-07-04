package service;

import java.util.HashMap;
import java.util.Map;

/**
 * Very small login check for the reception staff. Accounts are kept in
 * memory to keep things simple for a semester project - add more
 * usernames/passwords to the map below if more staff accounts are needed.
 */
public class AuthService {

    private final Map<String, String> accounts = new HashMap<>();

    public AuthService() {
        accounts.put("receptionist", "reception123");
        accounts.put("admin", "admin123");
    }

    public boolean login(String username, String password) {
        String storedPassword = accounts.get(username.trim());
        return storedPassword != null && storedPassword.equals(password);
    }
}
