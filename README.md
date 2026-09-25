# 🅿️ ParkEase

**ParkEase** is a web-based parking reservation system built with **Python Flask**. It allows users to check parking slot availability and book a parking slot for a specific date, time, and duration.

The application uses **SQLite for local development** and **PostgreSQL for production**, and is deployed using **Render**.

## 🚀 Live Demo

ParkEase is deployed and available online through Render.

**Live Application:** `https://parkease-hcaf.onrender.com/`

**GitHub:** `https://github.com/DanieloTony/parkease`

---

## ✨ Features

- 🅿️ 10 parking slots (A1–A10)
- 🔎 Smart parking availability search
- 📅 Date-based booking
- ⏰ Time-based booking
- ⌛ Duration-based booking
- 🚫 Prevents overlapping bookings
- 🟢 Available slot status
- 🟡 Upcoming booking status
- 🔴 Occupied slot status
- ⏱️ Live booking countdown
- 🎫 Booking confirmation
- 📱 Responsive user interface
- 🗄️ SQLite support for local development
- 🐘 PostgreSQL support for production
- 🚀 Cloud deployment using Render

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite, PostgreSQL |
| Server | Gunicorn |
| Deployment | Render |
| Version Control | Git, GitHub |

---

## 📂 Project Structure

```text
parkease/
│
├── app.py
├── requirements.txt
├── .gitignore
│
├── templates/
│   ├── index.html
│   ├── booking.html
│   ├── success.html
│   └── error.html
│
└── static/
    └── style.css
```

---

## 🔄 How It Works

```text
User
  │
  ▼
Select Date, Time & Duration
  │
  ▼
Check Parking Availability
  │
  ▼
Select Parking Slot
  │
  ▼
Enter Booking Details
  │
  ▼
Check Booking Conflict
  │
  ├── Conflict → Reject Booking
  │
  └── Available
          │
          ▼
     Create Booking
          │
          ▼
   Booking Confirmation
```

---

## 🚫 Booking Conflict Detection

ParkEase prevents multiple overlapping bookings for the same parking slot.

For example:

```text
Existing Booking
10:00 AM ───────── 12:00 PM

New Booking
11:00 AM ───────── 01:00 PM

Result: Booking rejected
```

A booking for a different time can still be accepted:

```text
Existing Booking
10:00 AM ───────── 12:00 PM

New Booking
12:00 PM ───────── 02:00 PM

Result: Booking accepted
```

---

## 🗄️ Database

The application contains two main tables.

### Slots

Stores the available parking slots.

```text
id
slot_number
```

### Bookings

Stores parking reservations.

```text
id
slot_id
name
phone
start_datetime
end_datetime
duration_hours
```

The `slot_id` connects each booking to its parking slot.

---

## 💾 Database Configuration

### Local Development

The application uses SQLite when `DATABASE_URL` is not configured.

```text
Flask
  ↓
SQLite
  ↓
parking.db
```

### Production

The application automatically uses PostgreSQL when `DATABASE_URL` is configured.

```text
Flask
  ↓
PostgreSQL
```

This allows the same application to run locally and in production.

---

## 🔐 Environment Variable

Production requires:

```text
DATABASE_URL
```

Example:

```text
DATABASE_URL=<your-postgresql-connection-url>
```

Do not commit database credentials, passwords, or `.env` files to GitHub.

---

## ▶️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/DanieloTony/parkease.git
```

### 2. Open the project

```bash
cd parkease
```

### 3. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

---

## 📦 Dependencies

The project uses:

```text
Flask
gunicorn
psycopg[binary]
```

Install them using:

```bash
pip install -r requirements.txt
```

---

## 🚀 Deployment

ParkEase is deployed using **Render**.

Production architecture:

```text
GitHub
   │
   ▼
Render Web Service
   │
   ▼
Gunicorn
   │
   ▼
Flask Application
   │
   ▼
PostgreSQL
```

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
gunicorn app:app
```

---

## 🧪 Booking Flow

1. Open ParkEase
2. Select a date
3. Select a starting time
4. Select booking duration
5. Search for available slots
6. Select a parking slot
7. Enter name and phone number
8. Confirm the booking
9. Receive the booking confirmation
10. View the updated parking status

---

## 🎯 Project Objectives

This project was built to practice and demonstrate:

- Python programming
- Flask backend development
- HTML, CSS and JavaScript
- SQL and relational databases
- SQLite
- PostgreSQL
- Database relationships
- Booking and scheduling logic
- Conflict detection
- Form handling
- Server-side validation
- Git and GitHub
- Production deployment
- Gunicorn
- Environment-based configuration

---

## 🔮 Future Improvements

Possible future enhancements:

- User authentication
- Admin dashboard
- Booking cancellation
- Booking history
- Email notifications
- Online payment
- Parking analytics
- Automated tests
- Docker support

---

## 👨‍💻 Author

**Danielo Tony S.**

B.Tech — Artificial Intelligence & Data Science

Interested in:

- Python
- Data Science
- Machine Learning
- Backend Development
- Artificial Intelligence

---

## ⭐ Project

Built with **Python, Flask, PostgreSQL, HTML, CSS and JavaScript**.
