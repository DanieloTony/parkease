from flask import Flask, render_template, request
import sqlite3
import os
from datetime import datetime, timedelta


# ==================================================
# FLASK APP
# ==================================================

app = Flask(__name__)


# ==================================================
# DATABASE CONFIGURATION
# ==================================================

DATABASE = "parking.db"

DATABASE_URL = os.environ.get("DATABASE_URL")

USE_POSTGRES = DATABASE_URL is not None


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_db_connection():

    # --------------------------------------------------
    # POSTGRESQL
    # --------------------------------------------------

    if USE_POSTGRES:

        import psycopg
        from psycopg.rows import dict_row

        connection = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row
        )

        return connection


    # --------------------------------------------------
    # SQLITE
    # --------------------------------------------------

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==================================================
# EXECUTE QUERY
# ==================================================

def execute_query(
    connection,
    query,
    parameters=()
):

    # PostgreSQL uses %s instead of ?
    if USE_POSTGRES:

        query = query.replace(
            "?",
            "%s"
        )

    return connection.execute(
        query,
        parameters
    )


# ==================================================
# CREATE DATABASE
# ==================================================

def create_database():

    connection = get_db_connection()


    # ==================================================
    # SQLITE DATABASE
    # ==================================================

    if not USE_POSTGRES:

        # --------------------------------------------------
        # SLOTS
        # --------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS slots (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                slot_number TEXT NOT NULL UNIQUE

            )
        """)


        # --------------------------------------------------
        # BOOKINGS
        # --------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS bookings (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                slot_id INTEGER NOT NULL,

                name TEXT NOT NULL,

                phone TEXT NOT NULL,

                start_datetime TEXT NOT NULL,

                end_datetime TEXT NOT NULL,

                duration_hours INTEGER NOT NULL,

                FOREIGN KEY (slot_id)
                    REFERENCES slots(id)

            )
        """)


    # ==================================================
    # POSTGRESQL DATABASE
    # ==================================================

    else:

        # --------------------------------------------------
        # SLOTS
        # --------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS slots (

                id SERIAL PRIMARY KEY,

                slot_number TEXT NOT NULL UNIQUE

            )
        """)


        # --------------------------------------------------
        # BOOKINGS
        # --------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS bookings (

                id SERIAL PRIMARY KEY,

                slot_id INTEGER NOT NULL,

                name TEXT NOT NULL,

                phone TEXT NOT NULL,

                start_datetime TEXT NOT NULL,

                end_datetime TEXT NOT NULL,

                duration_hours INTEGER NOT NULL,

                FOREIGN KEY (slot_id)
                    REFERENCES slots(id)

            )
        """)


    # ==================================================
    # CHECK EXISTING SLOTS
    # ==================================================

    result = execute_query(
        connection,

        """
        SELECT COUNT(*) AS total
        FROM slots
        """
    ).fetchone()


    existing_slots = result["total"]


    # ==================================================
    # CREATE A1 - A10
    # ==================================================

    if existing_slots == 0:

        for i in range(1, 11):

            execute_query(
                connection,

                """
                INSERT INTO slots (
                    slot_number
                )

                VALUES (?)
                """,

                (
                    f"A{i}",
                )
            )


    # ==================================================
    # SAVE
    # ==================================================

    connection.commit()

    connection.close()


# ==================================================
# CHECK SLOT BOOKING CONFLICT
# ==================================================

def check_slot_conflict(
    connection,
    slot_id,
    start_datetime,
    end_datetime
):

    booking = execute_query(
        connection,

        """
        SELECT *

        FROM bookings

        WHERE slot_id = ?

        AND start_datetime < ?

        AND end_datetime > ?

        LIMIT 1
        """,

        (
            slot_id,
            end_datetime,
            start_datetime
        )
    ).fetchone()


    return booking


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/")
def home():

    connection = get_db_connection()


    # ==================================================
    # GET PARKING SLOTS
    # ==================================================

    slots = execute_query(
        connection,

        """
        SELECT *

        FROM slots

        ORDER BY id
        """
    ).fetchall()


    # ==================================================
    # SEARCH PARAMETERS
    # ==================================================

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


    search_active = False

    search_start = None

    search_end = None


    # ==================================================
    # SMART AVAILABILITY SEARCH
    # ==================================================

    if (
        selected_date
        and selected_time
        and selected_duration
    ):

        try:

            duration_hours = int(
                selected_duration
            )


            search_start = datetime.strptime(
                f"{selected_date} {selected_time}",

                "%Y-%m-%d %H:%M"
            )


            search_end = (
                search_start
                +
                timedelta(
                    hours=duration_hours
                )
            )


            search_active = True


        except ValueError:

            search_active = False


    # ==================================================
    # CURRENT TIME
    # ==================================================

    now = datetime.now()


    now_string = now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # ==================================================
    # SLOT DATA
    # ==================================================

    slot_data = []


    for slot in slots:


        # ==================================================
        # FIND CURRENT / NEXT BOOKING
        # ==================================================

        current_booking = execute_query(

            connection,

            """
            SELECT *

            FROM bookings

            WHERE slot_id = ?

            AND end_datetime > ?

            ORDER BY start_datetime ASC

            LIMIT 1
            """,

            (
                slot["id"],
                now_string
            )

        ).fetchone()


        # ==================================================
        # DEFAULT STATE
        # ==================================================

        booking_state = "available"


        # ==================================================
        # CHECK BOOKING STATE
        # ==================================================

        if current_booking:


            booking_start = datetime.strptime(

                current_booking[
                    "start_datetime"
                ],

                "%Y-%m-%d %H:%M:%S"

            )


            booking_end = datetime.strptime(

                current_booking[
                    "end_datetime"
                ],

                "%Y-%m-%d %H:%M:%S"

            )


            # --------------------------------------------------
            # UPCOMING BOOKING
            # --------------------------------------------------

            if booking_start > now:

                booking_state = "upcoming"


            # --------------------------------------------------
            # CURRENTLY OCCUPIED
            # --------------------------------------------------

            elif (
                booking_start <= now
                and
                now < booking_end
            ):

                booking_state = "occupied"


        # ==================================================
        # SEARCH CONFLICT
        # ==================================================

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


        # ==================================================
        # STORE SLOT DATA
        # ==================================================

        slot_data.append({

            "id":
                slot["id"],

            "slot_number":
                slot["slot_number"],

            "current_booking":
                current_booking,

            "booking_state":
                booking_state,

            "search_conflict":
                search_conflict

        })


    # ==================================================
    # CLOSE DATABASE
    # ==================================================

    connection.close()


    # ==================================================
    # RENDER HOME PAGE
    # ==================================================

    return render_template(

        "index.html",

        slots=slot_data,

        selected_date=
            selected_date,

        selected_time=
            selected_time,

        selected_duration=
            selected_duration,

        search_active=
            search_active,

        search_start=
            search_start,

        search_end=
            search_end

    )


# ==================================================
# BOOKING PAGE
# ==================================================

@app.route(
    "/book/<int:slot_id>"
)
def book_page(slot_id):

    connection = get_db_connection()


    # ==================================================
    # GET SLOT
    # ==================================================

    slot = execute_query(

        connection,

        """
        SELECT *

        FROM slots

        WHERE id = ?

        """,

        (
            slot_id,
        )

    ).fetchone()


    connection.close()


    # ==================================================
    # SLOT NOT FOUND
    # ==================================================

    if slot is None:

        return (
            "Slot not found",
            404
        )


    # ==================================================
    # SEARCH VALUES
    # ==================================================

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


    # ==================================================
    # RENDER BOOKING PAGE
    # ==================================================

    return render_template(

        "booking.html",

        slot=slot,

        selected_date=
            selected_date,

        selected_time=
            selected_time,

        selected_duration=
            selected_duration

    )


# ==================================================
# CREATE BOOKING
# ==================================================

@app.route(
    "/book",
    methods=["POST"]
)
def book_slot():


    # ==================================================
    # GET FORM DATA
    # ==================================================

    slot_id = request.form[
        "slot_id"
    ]


    name = request.form[
        "name"
    ]


    phone = request.form[
        "phone"
    ]


    booking_date = request.form[
        "booking_date"
    ]


    booking_time = request.form[
        "booking_time"
    ]


    duration_hours = int(
        request.form[
            "duration_hours"
        ]
    )


    # ==================================================
    # CREATE START DATETIME
    # ==================================================

    start_datetime = datetime.strptime(

        f"{booking_date} {booking_time}",

        "%Y-%m-%d %H:%M"

    )


    # ==================================================
    # CREATE END DATETIME
    # ==================================================

    end_datetime = (

        start_datetime

        +

        timedelta(
            hours=duration_hours
        )

    )


    # ==================================================
    # DATABASE DATE STRINGS
    # ==================================================

    start_string = start_datetime.strftime(

        "%Y-%m-%d %H:%M:%S"

    )


    end_string = end_datetime.strftime(

        "%Y-%m-%d %H:%M:%S"

    )


    # ==================================================
    # OPEN DATABASE
    # ==================================================

    connection = get_db_connection()


    # ==================================================
    # CHECK BOOKING CONFLICT
    # ==================================================

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


    # ==================================================
    # GET SLOT
    # ==================================================

    slot = execute_query(

        connection,

        """

        SELECT *

        FROM slots

        WHERE id = ?

        """,

        (
            slot_id,
        )

    ).fetchone()


    if slot is None:

        connection.close()


        return (
            "Slot not found",
            404
        )


    # ==================================================
    # INSERT BOOKING
    # ==================================================

    if USE_POSTGRES:


        # --------------------------------------------------
        # POSTGRESQL
        # --------------------------------------------------

        cursor = execute_query(

            connection,

            """

            INSERT INTO bookings (

                slot_id,

                name,

                phone,

                start_datetime,

                end_datetime,

                duration_hours

            )

            VALUES (

                ?,
                ?,
                ?,
                ?,
                ?,
                ?

            )

            RETURNING id

            """,

            (

                slot_id,

                name,

                phone,

                start_string,

                end_string,

                duration_hours

            )

        )


        booking_id = cursor.fetchone()[
            "id"
        ]


    else:


        # --------------------------------------------------
        # SQLITE
        # --------------------------------------------------

        cursor = execute_query(

            connection,

            """

            INSERT INTO bookings (

                slot_id,

                name,

                phone,

                start_datetime,

                end_datetime,

                duration_hours

            )

            VALUES (

                ?,
                ?,
                ?,
                ?,
                ?,
                ?

            )

            """,

            (

                slot_id,

                name,

                phone,

                start_string,

                end_string,

                duration_hours

            )

        )


        booking_id = cursor.lastrowid


    # ==================================================
    # SAVE BOOKING
    # ==================================================

    connection.commit()

    connection.close()


    # ==================================================
    # SUCCESS PAGE
    # ==================================================

    return render_template(

        "success.html",

        booking_id=
            booking_id,

        slot=
            slot,

        name=
            name,

        phone=
            phone,

        start_datetime=
            start_datetime.strftime(
                "%d-%m-%Y %I:%M %p"
            ),

        end_datetime=
            end_datetime.strftime(
                "%d-%m-%Y %I:%M %p"
            ),

        duration_hours=
            duration_hours

    )


# ==================================================
# INITIALIZE DATABASE
# ==================================================

create_database()


# ==================================================
# LOCAL DEVELOPMENT
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )