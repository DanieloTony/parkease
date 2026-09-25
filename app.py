from flask import Flask, render_template, request
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE = "parking.db"


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# --------------------------------------------------
# CREATE DATABASE
# --------------------------------------------------

def create_database():

    connection = get_db_connection()

    # Slots table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_number TEXT NOT NULL UNIQUE
        )
    """)

    # Bookings table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            start_datetime TEXT NOT NULL,
            end_datetime TEXT NOT NULL,
            duration_hours INTEGER NOT NULL,
            FOREIGN KEY (slot_id) REFERENCES slots(id)
        )
    """)

    # Create A1 - A10 only if slots don't exist
    existing_slots = connection.execute(
        "SELECT COUNT(*) FROM slots"
    ).fetchone()[0]

    if existing_slots == 0:

        for i in range(1, 11):

            connection.execute(
                """
                INSERT INTO slots (slot_number)
                VALUES (?)
                """,
                (f"A{i}",)
            )

    connection.commit()
    connection.close()


# --------------------------------------------------
# CHECK BOOKING CONFLICT
# --------------------------------------------------

def check_slot_conflict(
    connection,
    slot_id,
    start_datetime,
    end_datetime
):

    booking = connection.execute("""
        SELECT *
        FROM bookings
        WHERE slot_id = ?

        AND start_datetime < ?

        AND end_datetime > ?

        LIMIT 1
    """, (
        slot_id,
        end_datetime,
        start_datetime
    )).fetchone()

    return booking


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():

    connection = get_db_connection()

    slots = connection.execute("""
        SELECT *
        FROM slots
        ORDER BY id
    """).fetchall()

    # --------------------------------------------------
    # SEARCH PARAMETERS
    # --------------------------------------------------

    selected_date = request.args.get("date", "")
    selected_time = request.args.get("time", "")
    selected_duration = request.args.get("duration", "")

    search_active = False

    search_start = None
    search_end = None

    # --------------------------------------------------
    # SMART AVAILABILITY SEARCH
    # --------------------------------------------------

    if (
        selected_date
        and selected_time
        and selected_duration
    ):

        try:

            duration_hours = int(selected_duration)

            search_start = datetime.strptime(
                f"{selected_date} {selected_time}",
                "%Y-%m-%d %H:%M"
            )

            search_end = (
                search_start
                + timedelta(hours=duration_hours)
            )

            search_active = True

        except ValueError:

            search_active = False

    # --------------------------------------------------
    # CURRENT TIME
    # --------------------------------------------------

    now = datetime.now()

    now_string = now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # --------------------------------------------------
    # SLOT DATA
    # --------------------------------------------------

    slot_data = []

    for slot in slots:

        # --------------------------------------------------
        # FIND CURRENT OR NEXT BOOKING
        #
        # This is the important part.
        #
        # Previously we only searched for an active
        # booking.
        #
        # Now we also find FUTURE bookings.
        # --------------------------------------------------

        current_booking = connection.execute("""
            SELECT *
            FROM bookings

            WHERE slot_id = ?

            AND end_datetime > ?

            ORDER BY start_datetime ASC

            LIMIT 1
        """, (
            slot["id"],
            now_string
        )).fetchone()

        # --------------------------------------------------
        # DETERMINE SLOT STATE
        # --------------------------------------------------

        booking_state = "available"

        if current_booking:

            booking_start = datetime.strptime(
                current_booking["start_datetime"],
                "%Y-%m-%d %H:%M:%S"
            )

            booking_end = datetime.strptime(
                current_booking["end_datetime"],
                "%Y-%m-%d %H:%M:%S"
            )

            # Booking has not started yet
            if booking_start > now:

                booking_state = "upcoming"

            # Booking is currently active
            elif (
                booking_start <= now
                and now < booking_end
            ):

                booking_state = "occupied"

        # --------------------------------------------------
        # SEARCH CONFLICT
        # --------------------------------------------------

        search_conflict = None

        if search_active:

            search_conflict = check_slot_conflict(
                connection,
                slot["id"],
                search_start.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                search_end.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        # --------------------------------------------------
        # STORE SLOT INFORMATION
        # --------------------------------------------------

        slot_data.append({

            "id": slot["id"],

            "slot_number": slot["slot_number"],

            "current_booking": current_booking,

            "booking_state": booking_state,

            "search_conflict": search_conflict
        })

    connection.close()

    # --------------------------------------------------
    # RENDER PAGE
    # --------------------------------------------------

    return render_template(
        "index.html",

        slots=slot_data,

        selected_date=selected_date,

        selected_time=selected_time,

        selected_duration=selected_duration,

        search_active=search_active,

        search_start=search_start,

        search_end=search_end
    )


# --------------------------------------------------
# BOOKING PAGE
# --------------------------------------------------

@app.route("/book/<int:slot_id>")
def book_page(slot_id):

    connection = get_db_connection()

    slot = connection.execute("""
        SELECT *
        FROM slots
        WHERE id = ?
    """, (
        slot_id,
    )).fetchone()

    connection.close()

    if slot is None:

        return "Slot not found", 404

    # Get values from smart search
    selected_date = request.args.get(
        "date",
        ""
    )

    selected_time = request.args.get(
        "time",
        ""
    )

    selected_duration = request.args.get(
        "duration",
        ""
    )

    return render_template(
        "booking.html",

        slot=slot,

        selected_date=selected_date,

        selected_time=selected_time,

        selected_duration=selected_duration
    )


# --------------------------------------------------
# CREATE BOOKING
# --------------------------------------------------

@app.route("/book", methods=["POST"])
def book_slot():

    slot_id = request.form["slot_id"]

    name = request.form["name"]

    phone = request.form["phone"]

    booking_date = request.form["booking_date"]

    booking_time = request.form["booking_time"]

    duration_hours = int(
        request.form["duration_hours"]
    )

    # --------------------------------------------------
    # CREATE START DATETIME
    # --------------------------------------------------

    start_datetime = datetime.strptime(
        f"{booking_date} {booking_time}",
        "%Y-%m-%d %H:%M"
    )

    # --------------------------------------------------
    # CREATE END DATETIME
    # --------------------------------------------------

    end_datetime = (
        start_datetime
        + timedelta(hours=duration_hours)
    )

    start_string = start_datetime.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    end_string = end_datetime.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection = get_db_connection()

    # --------------------------------------------------
    # CHECK FOR CONFLICT
    # --------------------------------------------------

    existing_booking = check_slot_conflict(
        connection,

        slot_id,

        start_string,

        end_string
    )

    if existing_booking:

        connection.close()

        return render_template(
            "error.html",

            message=(
                "This slot is already booked "
                "during the selected time."
            )
        )

    # --------------------------------------------------
    # GET SLOT
    # --------------------------------------------------

    slot = connection.execute("""
        SELECT *
        FROM slots
        WHERE id = ?
    """, (
        slot_id,
    )).fetchone()

    if slot is None:

        connection.close()

        return "Slot not found", 404

    # --------------------------------------------------
    # INSERT BOOKING
    # --------------------------------------------------

    cursor = connection.execute("""
        INSERT INTO bookings (
            slot_id,
            name,
            phone,
            start_datetime,
            end_datetime,
            duration_hours
        )

        VALUES (?, ?, ?, ?, ?, ?)
    """, (

        slot_id,

        name,

        phone,

        start_string,

        end_string,

        duration_hours
    ))

    booking_id = cursor.lastrowid

    connection.commit()

    connection.close()

    # --------------------------------------------------
    # SUCCESS PAGE
    # --------------------------------------------------

    return render_template(

        "success.html",

        booking_id=booking_id,

        slot=slot,

        name=name,

        phone=phone,

        start_datetime=start_datetime.strftime(
            "%d-%m-%Y %I:%M %p"
        ),

        end_datetime=end_datetime.strftime(
            "%d-%m-%Y %I:%M %p"
        ),

        duration_hours=duration_hours
    )


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    create_database()

    app.run(
        debug=True
    )