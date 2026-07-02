# ============================================
# FILE: admin.py
# Admin functions - CRUD operations for movies
# ============================================

from csv_handler import *

def view_movies():
    """Display all movies in a nice table format"""
    movies = read_movies()
    
    if not movies:
        print("\nNo movies available in the system!")
        return
    
    print("\n" + "="*65)
    print("MOVIE LIST")
    print("="*65)
    print(f"{'ID':<6} {'Movie Name':<25} {'Genre':<12} {'Time':<12} {'Seats':<8} {'Price':<8}")
    print("-"*65)
    
    for movie in movies:
        print(f"{movie['MovieID']:<6} {movie['MovieName']:<25} {movie['Genre']:<12} {movie['Time']:<12} {movie['Seats']:<8} {movie['Price']:<8}")

def add_movie():
    """Add a new movie to the system"""
    movies = read_movies()
    
    print("\n" + "="*40)
    print("ADD NEW MOVIE")
    print("="*40)
    
    # Get movie details from user
    movie_id = input("Enter Movie ID: ")
    
    # Check if Movie ID already exists
    for movie in movies:
        if movie["MovieID"] == movie_id:
            print("❌ Movie ID already exists!")
            return
    
    movie_name = input("Enter Movie Name: ")
    genre = input("Enter Genre: ")
    time = input("Enter Show Time: ")
    seats = input("Enter Total Seats: ")
    price = input("Enter Ticket Price: ")
    
    # Create new movie record
    new_movie = {
        "MovieID": movie_id,
        "MovieName": movie_name,
        "Genre": genre,
        "Time": time,
        "Seats": seats,
        "Price": price
    }
    
    movies.append(new_movie)
    write_movies(movies)
    
    print("\n✅ Movie added successfully!")

def delete_movie():
    """Delete a movie from the system"""
    movies = read_movies()
    
    if not movies:
        print("\nNo movies to delete!")
        return
    
    view_movies()
    print("\n" + "="*40)
    print("DELETE MOVIE")
    print("="*40)
    
    movie_id = input("Enter Movie ID to delete: ")
    
    # Check if movie exists
    movie_found = False
    for movie in movies:
        if movie["MovieID"] == movie_id:
            movie_found = True
            break
    
    if not movie_found:
        print("❌ Movie not found!")
        return
    
    # Ask for confirmation
    confirm = input(f"Are you sure you want to delete this movie? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ Operation cancelled!")
        return
    
    # Remove the movie
    updated_movies = []
    for movie in movies:
        if movie["MovieID"] != movie_id:
            updated_movies.append(movie)
    
    write_movies(updated_movies)
    print("\n✅ Movie deleted successfully!")

def update_movie():
    """Update movie details"""
    movies = read_movies()
    
    if not movies:
        print("\nNo movies to update!")
        return
    
    view_movies()
    print("\n" + "="*40)
    print("UPDATE MOVIE")
    print("="*40)
    
    movie_id = input("Enter Movie ID to update: ")
    
    # Find the movie
    found = False
    for movie in movies:
        if movie["MovieID"] == movie_id:
            found = True
            print(f"\nCurrent Name: {movie['MovieName']}")
            new_name = input("Enter new name (Press Enter to keep current): ")
            if new_name:
                movie["MovieName"] = new_name
            
            print(f"Current Genre: {movie['Genre']}")
            new_genre = input("Enter new genre (Press Enter to keep current): ")
            if new_genre:
                movie["Genre"] = new_genre
            
            print(f"Current Time: {movie['Time']}")
            new_time = input("Enter new time (Press Enter to keep current): ")
            if new_time:
                movie["Time"] = new_time
            
            print(f"Current Seats: {movie['Seats']}")
            new_seats = input("Enter new seats (Press Enter to keep current): ")
            if new_seats:
                movie["Seats"] = new_seats
            
            print(f"Current Price: {movie['Price']}")
            new_price = input("Enter new price (Press Enter to keep current): ")
            if new_price:
                movie["Price"] = new_price
            
            write_movies(movies)
            print("\n✅ Movie updated successfully!")
            break
    
    if not found:
        print("❌ Movie not found!")