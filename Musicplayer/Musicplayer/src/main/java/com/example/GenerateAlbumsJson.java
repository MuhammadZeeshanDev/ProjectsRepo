package com.example;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

class Album {
    String album;      
    String title;      
    String cover;      
    List<Song> songs;  

    Album(String folderName) {
        this.album = folderName;
        this.title = folderName;
        this.songs = new ArrayList<>();
    }
}

class Song {
    String title;
    String artist;
    String filename;

    Song(String title, String artist, String filename) {
        this.title = title;
        this.artist = artist;
        this.filename = filename;
    }
}

public class GenerateAlbumsJson {

    private static final String[] AUDIO_EXTENSIONS = {".mp3", ".mpeg", ".wav", ".m4a", ".flac"};

    public static void main(String[] args) throws IOException {
        File songsFolder = new File("frontend/Songs"); // folder with albums
        File outputFolder = new File("frontend/generated"); // JSON output folder
        if (!outputFolder.exists()) outputFolder.mkdirs();

        if (!songsFolder.exists()) {
            System.err.println("Songs folder not found: " + songsFolder.getAbsolutePath());
            return;
        }

        File[] albums = songsFolder.listFiles(File::isDirectory);
        if (albums == null || albums.length == 0) {
            System.out.println("No albums found in " + songsFolder.getAbsolutePath());
            return;
        }

        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        List<Album> albumList = new ArrayList<>();

        for (File albumDir : albums) {
            Album album = new Album(albumDir.getName());

            // Find cover image (file starting with "cover")
            for (File f : albumDir.listFiles()) {
                if (f.isFile() && f.getName().toLowerCase().startsWith("cover")) {
                    album.cover = f.getName();
                    break;
                }
            }
     
            // Read songs
            File[] filesInAlbum = albumDir.listFiles();
            if (filesInAlbum != null) {
                for (File f : filesInAlbum) {
                    if (f.isFile() && isAudioFile(f.getName())) {
                        String filename = f.getName();

                        // Parse title and artist
                        String baseName = filename.substring(0, filename.lastIndexOf('.')).trim();
                        String title;
                        String artist;
                        int dashIndex = baseName.lastIndexOf('-');
                        if (dashIndex != -1) {
                            title = baseName.substring(0, dashIndex).trim();
                            artist = baseName.substring(dashIndex + 1).trim();
                        } else {
                            title = baseName;
                            artist = "Unknown";
                        }

                        // Use relative path so frontend can play the file
                        String relativePath = "Songs/" + album.album + "/" + filename;
                        album.songs.add(new Song(title, artist, relativePath));
                    }
                }
            }

            // Write individual album JSON
            File albumJson = new File(outputFolder, album.album + ".json");
            try (FileWriter writer = new FileWriter(albumJson)) {
                gson.toJson(album, writer);
            }

            albumList.add(album);
        }

        // Write index JSON containing all albums
        File indexJson = new File(outputFolder, "albums.json");
        try (FileWriter writer = new FileWriter(indexJson)) {
            gson.toJson(albumList, writer);
        }

        System.out.println("Generated JSON for " + albumList.size() + " albums in " + outputFolder.getAbsolutePath());
    }

    // Helper method to check if file is a supported audio file
    private static boolean isAudioFile(String filename) {
        String lower = filename.toLowerCase();
        for (String ext : AUDIO_EXTENSIONS) {
            if (lower.endsWith(ext)) return true;
        }
        return false;
    }
}
