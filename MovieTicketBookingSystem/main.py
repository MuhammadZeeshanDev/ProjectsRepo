# ============================================
# FILE: main.py
# Main program - Entry point
# ============================================

import os
from admin import *
from customer import *

# Admin password (you can change this)
ADMIN_PASSWORD = "admin123"

def main():
    """Main menu of the application"""
    
    # Check if we need to create sample data
    if not os.path.exists("movies.csv"):
        print("\n📁 Creating sample data...")
        sample_movies = [
            {"MovieID": "101", "MovieName": "Avengers: Endgame", "Genre": "Action", "Time": "6:00 PM", "Seats": "50", "Price": "800"},
            {"MovieID": "102", "MovieName": "The Batman", "Genre": "Action", "Time": "9:00 PM", "Seats": "40", "Price": "700"},
            {"MovieID": "103", "MovieName": "Frozen II", "Genre": "Animation", "Time": "3:00 PM", "Seats": "60", "Price": "500"},
            {"MovieID": "104", "MovieName": "Spider-Man", "Genre": "Action", "Time": "7:00 PM", "Seats": "45", "Price": "750"},
            {"MovieID": "105", "MovieName": "Toy Story 4", "Genre": "Animation", "Time": "2:00 PM", "Seats": "55", "Price": "550"}
        ]
        write_movies(sample_movies)
        print("✅ Sample movies created!")
    
    # Main program loop
    while True:
        print("\n" + "="*50)
        print("   🎬 MOVIE TICKET BOOKING SYSTEM")
        print("="*50)
        print("1. View Movies")
        print("2. Book Ticket")
        print("3. View Bookings")
        print("4. Cancel Booking")
        print("5. Admin Panel")
        print("6. Exit")
        print("="*50)
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            show_movies()
            input("\nPress Enter to continue...")
            
        elif choice == "2":
            book_ticket()
            input("\nPress Enter to continue...")
            
        elif choice == "3":
            view_bookings()
            input("\nPress Enter to continue...")
            
        elif choice == "4":
            cancel_booking()
            input("\nPress Enter to continue...")
            
        elif choice == "5":
            password = input("\nEnter Admin Password: ")
            
            if password == ADMIN_PASSWORD:
                admin_panel()
            else:
                print("❌ Wrong password!")
                input("\nPress Enter to continue...")
            
        elif choice == "6":
            print("\n" + "="*50)
            print("👋 Thank you for using the system!")
            print("   Have a great day!")
            print("="*50)
            break
            
        else:
            print("❌ Invalid choice! Please try again.")
            input("\nPress Enter to continue...")

def admin_panel():
    """Admin menu for managing movies"""
    while True:
        print("\n" + "="*50)
        print("   🔐 ADMIN PANEL")
        print("="*50)
        print("1. View All Movies")
        print("2. Add New Movie")
        print("3. Delete Movie")
        print("4. Update Movie")
        print("5. Back to Main Menu")
        print("="*50)
        
        admin_choice = input("Enter your choice (1-5): ")
        
        if admin_choice == "1":
            view_movies()
            input("\nPress Enter to continue...")
            
        elif admin_choice == "2":
            add_movie()
            input("\nPress Enter to continue...")
            
        elif admin_choice == "3":
            delete_movie()
            input("\nPress Enter to continue...")
            
        elif admin_choice == "4":
            update_movie()
            input("\nPress Enter to continue...")
            
        elif admin_choice == "5":
            break
            
        else:
            print("❌ Invalid choice!")
            input("\nPress Enter to continue...")

# Start the program
if __name__ == "__main__":
    print("\n" + "="*50)
    print("   WELCOME TO MOVIE TICKET BOOKING")
    print("   Semester Project - Python")
    print("="*50)
    main()