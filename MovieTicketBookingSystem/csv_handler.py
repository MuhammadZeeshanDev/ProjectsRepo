# ============================================
# FILE: csv_handler.py
# Handles all the CSV file operations
# ============================================

import csv
import os

# File paths - keeping it simple with relative paths
MOVIE_FILE = "movies.csv"
BOOKING_FILE = "bookings.csv"

def read_movies():
    """Read movies from CSV file"""
    movies = []
    
    # Check if file exists before reading
    if os.path.exists(MOVIE_FILE):
        with open(MOVIE_FILE, "r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                movies.append(row)
    
    return movies

def write_movies(movies):
    """Write movies back to CSV file"""
    with open(MOVIE_FILE, "w", newline="") as file:
        fieldnames = ["MovieID", "MovieName", "Genre", "Time", "Seats", "Price"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(movies)

def read_bookings():
    """Read bookings from CSV file"""
    bookings = []
    
    if os.path.exists(BOOKING_FILE):
        with open(BOOKING_FILE, "r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                bookings.append(row)
    
    return bookings

def write_bookings(bookings):
    """Write bookings to CSV file"""
    with open(BOOKING_FILE, "w", newline="") as file:
        fieldnames = ["BookingID", "CustomerName", "MovieID", "MovieName", "Tickets", "TotalPrice"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(bookings)

def add_booking(data):
    """Add a new booking to the system"""
    bookings = read_bookings()
    
    # Generate a new Booking ID
    if bookings:
        # Find the highest ID and add 1
        max_id = 0
        for b in bookings:
            if int(b["BookingID"]) > max_id:
                max_id = int(b["BookingID"])
        data["BookingID"] = str(max_id + 1)
    else:
        data["BookingID"] = "1"
    
    bookings.append(data)
    write_bookings(bookings)