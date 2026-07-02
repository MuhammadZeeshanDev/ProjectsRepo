# ============================================
# FILE: customer.py
# Customer functions - Booking operations
# ============================================

from csv_handler import *

def show_movies():
    """Display movies for customers (only available ones)"""
    movies = read_movies()
    
    if not movies:
        print("\nNo movies available!")
        return
    
    print("\n" + "="*65)
    print("AVAILABLE MOVIES")
    print("="*65)
    print(f"{'ID':<6} {'Movie Name':<25} {'Genre':<12} {'Time':<12} {'Seats':<8} {'Price':<8}")
    print("-"*65)
    
    for movie in movies:
        # Show seats available, or show "SOLD OUT" if no seats left
        seats = movie['Seats']
        if int(seats) <= 0:
            seats = "SOLD OUT"
        print(f"{movie['MovieID']:<6} {movie['MovieName']:<25} {movie['Genre']:<12} {movie['Time']:<12} {seats:<8} {movie['Price']:<8}")

def book_ticket():
    """Book movie tickets"""
    movies = read_movies()
    
    if not movies:
        print("\nNo movies available for booking!")
        return
    
    show_movies()
    print("\n" + "="*40)
    print("BOOK TICKETS")
    print("="*40)
    
    # Get movie ID
    movie_id = input("Enter Movie ID: ")
    
    # Find the selected movie
    selected_movie = None
    for movie in movies:
        if movie["MovieID"] == movie_id:
            selected_movie = movie
            break
    
    if not selected_movie:
        print("❌ Movie not found!")
        return
    
    # Check if seats are available
    if int(selected_movie["Seats"]) <= 0:
        print("❌ Sorry, no seats available for this movie!")
        return
    
    # Get customer details
    customer_name = input("Enter Customer Name: ")
    
    # Get number of tickets
    tickets = input("Enter number of tickets: ")
    
    # Validate ticket count
    if not tickets.isdigit():
        print("❌ Invalid input! Please enter a number.")
        return
    
    tickets = int(tickets)
    
    if tickets <= 0:
        print("❌ Invalid ticket count!")
        return
    
    if tickets > int(selected_movie["Seats"]):
        print(f"❌ Only {selected_movie['Seats']} seats available!")
        return
    
    # Calculate total price
    total = tickets * int(selected_movie["Price"])
    
    # Update seats
    selected_movie["Seats"] = str(int(selected_movie["Seats"]) - tickets)
    
    # Create booking record
    booking = {
        "CustomerName": customer_name,
        "MovieID": selected_movie["MovieID"],
        "MovieName": selected_movie["MovieName"],
        "Tickets": tickets,
        "TotalPrice": total
    }
    
    # Save everything
    add_booking(booking)
    write_movies(movies)
    
    # Show confirmation
    print("\n" + "="*45)
    print("🎫 BOOKING CONFIRMATION")
    print("="*45)
    print(f"Booking ID: {booking['BookingID']}")
    print(f"Customer: {customer_name}")
    print(f"Movie: {selected_movie['MovieName']}")
    print(f"Tickets: {tickets}")
    print(f"Total Price: ${total}")
    print("="*45)
    print("✅ Booking successful! Enjoy the show!")

def view_bookings():
    """View all bookings"""
    bookings = read_bookings()
    
    if not bookings:
        print("\nNo bookings found!")
        return
    
    print("\n" + "="*70)
    print("BOOKING HISTORY")
    print("="*70)
    print(f"{'ID':<6} {'Customer':<20} {'Movie':<25} {'Tickets':<8} {'Total':<8}")
    print("-"*70)
    
    for booking in bookings:
        print(f"{booking['BookingID']:<6} {booking['CustomerName']:<20} {booking['MovieName']:<25} {booking['Tickets']:<8} ${booking['TotalPrice']:<8}")

def cancel_booking():
    """Cancel a booking and restore seats"""
    bookings = read_bookings()
    
    if not bookings:
        print("\nNo bookings to cancel!")
        return
    
    view_bookings()
    print("\n" + "="*40)
    print("CANCEL BOOKING")
    print("="*40)
    
    booking_id = input("Enter Booking ID to cancel: ")
    
    # Find the booking
    booking_to_cancel = None
    for booking in bookings:
        if booking["BookingID"] == booking_id:
            booking_to_cancel = booking
            break
    
    if not booking_to_cancel:
        print("❌ Booking not found!")
        return
    
    # Confirm cancellation
    confirm = input(f"Cancel booking for {booking_to_cancel['CustomerName']}? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ Cancellation cancelled!")
        return
    
    # Restore seats
    movies = read_movies()
    for movie in movies:
        if movie["MovieID"] == booking_to_cancel["MovieID"]:
            current_seats = int(movie["Seats"])
            returned_seats = int(booking_to_cancel["Tickets"])
            movie["Seats"] = str(current_seats + returned_seats)
            write_movies(movies)
            break
    
    # Remove booking
    updated_bookings = []
    for booking in bookings:
        if booking["BookingID"] != booking_id:
            updated_bookings.append(booking)
    
    write_bookings(updated_bookings)
    print(f"\n✅ Booking {booking_id} cancelled successfully!")
    print(f"   {booking_to_cancel['Tickets']} seats have been restored.")