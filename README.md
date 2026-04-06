# 📡 Smart Attendance System

> OTP + GPS geofence attendance marking with anomaly detection — built for college projects.

---

## 🗂 Project Structure

```
smart-attendance-system/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Flask entry point
│   │   ├── config.py                # All configuration
│   │   ├── database.py              # SQLite init + connection
│   │   ├── routes/
│   │   │   ├── session.py           # Teacher session management
│   │   │   ├── attendance.py        # Student attendance marking
│   │   │   └── teacher.py          # Reports & dashboard data
│   │   ├── services/
│   │   │   ├── otp_service.py       # OTP generation & verification
│   │   │   ├── geo_service.py       # GPS geofence validation
│   │   │   └── anomaly_detection.py # Fraud detection algorithms
│   │   └── utils/
│   │       └── haversine.py         # Great-circle distance formula
│   ├── tests/
│   │   └── test_services.py         # Unit tests (pytest)
│   └── requirements.txt
├── frontend/
│   ├── index.html                   # Full PWA (no build needed!)
│   ├── src/
│   │   ├── utils/api.js             # API client
│   │   ├── utils/deviceId.js        # Browser fingerprinting
│   │   └── hooks/useGeolocation.js  # GPS hook
│   └── package.json
├── database/
│   └── schema.sql                   # Full DB schema (MySQL/SQLite)
├── .github/workflows/ci.yml         # GitHub Actions CI/CD
├── .env.example                     # Environment variables template
└── README.md
```

---

## ⚡ Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/your-username/smart-attendance-system.git
cd smart-attendance-system
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example ../.env
# Edit .env with your classroom coordinates

# Run the server
cd app
python main.py
# → Running on http://localhost:5000
```

### 3. Frontend Setup

**Option A — No build required (fastest):**
```bash
# Just open frontend/index.html in your browser
# Make sure backend is running on localhost:5000
open frontend/index.html
```

**Option B — React dev server:**
```bash
cd frontend
npm install
npm start
# → Running on http://localhost:3000
```

### 4. Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## 🔌 API Reference

### Session Endpoints (Teacher)

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/session/start` | Start a new session, returns OTP |
| POST | `/session/refresh-otp/:id` | Generate fresh OTP |
| POST | `/session/end/:id` | End session |
| GET  | `/session/status/:id` | Get session status |

**Start Session payload:**
```json
{
  "teacher_id": "teacher_001",
  "subject": "Computer Networks",
  "lat": 28.7041,
  "lon": 77.1025,
  "radius": 100
}
```

### Attendance Endpoints (Student)

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/attendance/mark` | Mark attendance |
| GET  | `/attendance/list/:id` | List all records for session |

**Mark Attendance payload:**
```json
{
  "session_id": 1,
  "otp": "482910",
  "lat": 28.7040,
  "lon": 77.1026,
  "student_id": "2023CS042",
  "student_name": "Rahul Sharma",
  "device_id": "dev_a1b2c3"
}
```

### Teacher Dashboard Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/teacher/sessions/:teacher_id` | All sessions by teacher |
| GET | `/teacher/report/:session_id` | Full session report + stats |
| GET | `/teacher/flagged/:session_id` | Only flagged records |

---

## 🛡 Anti-Cheating System

The system detects the following fraud patterns:

| Flag | Trigger | Risk Weight |
|------|---------|-------------|
| `duplicate_device` | Same device submits for 2+ students | 50 |
| `coordinate_cluster` | 5+ students share identical GPS (±10m) | 40 |
| `impossible_speed` | Location changed too fast (>30 m/s) | 35 |
| `null_island` | GPS returns (0,0) — common mock default | 60 |

Risk is scored 0–100 and classified as **LOW / MEDIUM / HIGH**.

---

## 🔧 Configuration

Edit `backend/app/config.py` or use environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OTP_EXPIRY_SECONDS` | `60` | OTP validity window |
| `GEOFENCE_RADIUS` | `100` | Allowed distance in meters |
| `CLASSROOM_LAT` | `28.7041` | Classroom latitude |
| `CLASSROOM_LON` | `77.1025` | Classroom longitude |
| `SECRET_KEY` | (set this!) | Flask secret key |

---

## 🚀 Deployment

### Render (free tier)
1. Push to GitHub
2. Create a new Web Service on Render
3. Set build command: `pip install -r backend/requirements.txt`
4. Set start command: `gunicorn -w 4 -b 0.0.0.0:$PORT backend.app.main:app`

### Railway / Heroku
Use the same start command above with a `Procfile`:
```
web: gunicorn -w 4 backend.app.main:app
```

---

## 📊 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 3.0, Flask-CORS |
| Database | SQLite (dev) / MySQL or PostgreSQL (prod) |
| Frontend | React 18 (no build), Vanilla PWA |
| Auth | OTP (in-memory, rotating) |
| Location | Browser Geolocation API + Haversine |
| CI/CD | GitHub Actions |
| Testing | pytest |

---

## 📄 License

MIT — free for college and academic use.
