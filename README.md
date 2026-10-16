# 🎮 Hangman Game – Interactive Word Guessing Website

A modern, responsive, and full-stack interactive Hangman word-guessing web application built with **Python**, **Django**, **MySQL (via XAMPP)**, and vanilla **HTML5/CSS3/JavaScript**.

---

## 🌟 Features

- **Dynamic Secret Word Selection:** Randomly picks from a predefined list of 5 core tech terms (`PYTHON`, `DJANGO`, `COMPUTER`, `PROGRAM`, `DATABASE`) on the server.
- **Strict Security & Anti-Cheat:** Secret word is stored in the Django session and is **never** leaked to client-side HTML/JS until the round concludes.
- **Interactive UI & Visual Hangman:** Real-time vector SVG hangman drawing that dynamically builds up with each mistake (0 to 6 chances).
- **Responsive Virtual Keyboard:** Color-coded keyboard buttons (green for correct, red for incorrect) with physical keyboard support.
- **Robust Scoring System:** 
  $$\text{Score} = \max(0, 100 - (10 \times \text{incorrect guesses}))$$ for wins, $0$ points for losses.
- **Persistent MySQL Integration:** Saves every completed match with player statistics, attempts, scores, and timestamps.
- **User Authentication & Player Profiles:** Register and login to track your personal game history and compete on the global leaderboard.
- **Live Leaderboard:** Real-time player rankings with medal badges (🥇, 🥈, 🥉), win ratios, and aggregate scores.

---

## 🛠️ Technology Stack

- **Backend:** Python, Django 4.2 LTS
- **Database:** MySQL / MariaDB (managed via XAMPP & phpMyAdmin)
- **Frontend:** HTML5, CSS3 (Modern Flexbox & CSS Grid), JavaScript (Fetch API with CSRF protection)
- **Database Drivers:** `mysqlclient` and `PyMySQL`

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- XAMPP (Apache & MySQL)

### 2. Clone the Repository
```bash
git clone https://github.com/abhishekgadagin24-jpg/CodeAlpha_HangmanGame.git
cd CodeAlpha_HangmanGame
```

### 3. Create & Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Setup MySQL Database
1. Start **Apache** and **MySQL** in the XAMPP Control Panel.
2. Open `http://localhost/phpmyadmin/`.
3. Create a new database named `hangmandb` (collation: `utf8mb4_general_ci`).

### 6. Apply Migrations & Create Admin
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Run Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Automated Testing
Run the comprehensive suite of 14 automated unit and integration tests:
```bash
python manage.py test game
```

---

## 👤 Author
- **GitHub:** [@abhishekgadagin24-jpg](https://github.com/abhishekgadagin24-jpg)
