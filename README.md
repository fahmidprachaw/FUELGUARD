# FuelGuard — Petrol Pump Fuel Control System
> Django + DRF + OpenCV + pytesseract + Tailwind CSS

---

## 📁 Project Structure

```
petrol_pump/
├── manage.py
├── settings.py
├── urls.py
├── wsgi.py
├── db.sqlite3              ← auto-created after migrations
├── media/                  ← uploaded images (auto-created)
│   └── fuel_logs/
├── templates/
│   └── index.html          ← frontend UI
├── static/
│   └── js/
│       └── app.js          ← vanilla JS logic
└── app/
    ├── __init__.py
    ├── admin.py
    ├── models.py           ← Vehicle + FuelLog models
    ├── serializers.py      ← DRF serializers
    ├── views.py            ← API endpoint logic
    ├── utils.py            ← OCR with OpenCV + pytesseract
    └── urls.py             ← app URL routes
```

---

## ⚡ Quick Setup

### 1. Install Python dependencies

```bash
pip install django djangorestframework opencv-python pillow pytesseract
```

### 2. Install Tesseract OCR engine (required by pytesseract)

**Ubuntu / Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
Then add Tesseract to your PATH, or set in utils.py:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### 3. Run database migrations

```bash
cd petrol_pump
python manage.py makemigrations app
python manage.py migrate
```

### 4. Create a superuser (for /admin/ access)

```bash
python manage.py createsuperuser
```

### 5. Start the development server

```bash
python manage.py runserver
```

### 6. Open your browser

- **Frontend UI:** http://127.0.0.1:8000/
- **Admin panel:** http://127.0.0.1:8000/admin/
- **API endpoint:** http://127.0.0.1:8000/api/check-fuel/

---

## 🔌 API Reference

### POST `/api/check-fuel/`

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | File | No* | Vehicle number plate photo |
| `manual_number` | String | No* | Manual fallback number |

*At least one must be provided.

**Responses:**

```json
// ✅ Fuel allowed
{ "status": "allowed", "number": "DH1234AB", "fueled_at": "2024-01-15 14:30", "message": "Fuel dispensed." }

// 🚫 Fuel blocked (< 3 days since last fill)
{ "status": "blocked", "number": "DH1234AB", "last_fuel_date": "2024-01-14 10:00", "hours_remaining": 20, "message": "..." }

// ⚠️ Error (OCR failure, no input, etc.)
{ "status": "error", "message": "Number not detected." }
```

---

## 🧠 How OCR Works

1. Image uploaded → read as bytes
2. NumPy array decoded by OpenCV
3. Converted to grayscale
4. Adaptive threshold applied (improves contrast)
5. Small images scaled up 2x
6. Tesseract extracts text (`--psm 8` single-word mode)
7. Regex cleans result: only A-Z and 0-9 kept

---

## ⚙️ Configuration

Edit `settings.py` to change:
- `REFUEL_COOLDOWN_DAYS` in `views.py` (default: 3)
- `MEDIA_ROOT` for image storage location
- `SECRET_KEY` and `DEBUG=False` for production
