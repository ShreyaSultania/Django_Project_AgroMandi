# Agro AI System - Django REST Framework Backend

This is the production-ready Django REST Framework backend migrated from the Node.js / Express.js backend.

## 🚀 Key Features & Architecture
- **Framework:** Python 3.13 + Django 6.0 + Django REST Framework (DRF)
- **CORS Support:** `django-cors-headers` configured for seamless frontend communication
- **Machine Learning:** Scikit-learn Random Forest Regressors for future price & demand prediction (`predictions` app)
- **Caching:** Redis cache support with automated fallback for market prices (`prices` app)
- **Geocoding & Location:** OpenCage & OpenStreetMap reverse geocoding with local fallback (`locations` app)
- **Mandi Decision Matrix (DPS):** Dynamic Priority Score & transport cost evaluation (`mandis` app)
- **Weather Analysis:** OpenWeatherMap API integration with risk assessment heuristics (`weather` app)
- **Offline / Resilient Mode:** Packaged Agmarknet dataset fallback (`data/9ef84268-d588-465a-a308-a864a43d0070.csv`) ensures the application functions even when external government APIs are down or rate-limited.

---

## 📁 Apps Structure
```
django_backend/
├── agro_ai_backend/        # Project settings, wsgi, asgi, and master urls
├── core/                   # Shared models (Config weights), response utilities, seed commands
├── locations/              # Geocoding, reverse geocoding, distance calculations (/api/location/*)
├── mandis/                 # Mandis recommendation, transport cost, selection confirmation (/api/shipments/*)
├── prices/                 # Market commodity prices aggregation & caching (/api/prices)
├── weather/                # Weather condition fetching & risk scoring (/api/weather)
├── predictions/            # ML models & scenario simulation (/api/simulate)
├── data/                   # Synthetic training dataset & historical Agmarknet records
├── requirements.txt        # Python package dependencies
├── Dockerfile              # Container deployment file
└── manage.py
```

---

## 🛠️ How to Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your API keys (optional):
```bash
cp .env.example .env
```

### 3. Run Migrations & Seed Initial Data
```bash
python manage.py migrate
python manage.py seed_data
```

### 4. Start Development Server
```bash
python manage.py runserver
```
or explicitly:
```bash
python manage.py runserver 127.0.0.1:5000
```

> **Note for Windows:** Use `127.0.0.1:5000` or simply `python manage.py runserver` instead of `0.0.0.0:5000`. Windows blocks non-elevated (non-administrator) processes from binding globally to `0.0.0.0` with `Error: You don't have permission to access that port`. Binding to `127.0.0.1:5000` is unrestricted and matches the frontend URL.

The server runs on `http://localhost:5000`, exactly matching the frontend Vite proxy (`VITE_API_URL=http://localhost:5000/api`).

---

## 🧪 Testing & Validation
To execute the automated test suite covering all apps, algorithms, and endpoints:
```bash
python manage.py test
```

To run end-to-end endpoint verification:
```bash
python verify_endpoints.py
```
