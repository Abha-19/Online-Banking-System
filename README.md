# NorthStar Bank

NorthStar Bank is a polished Flask-based online banking application with a professional dashboard experience for both customers and administrators.

## Highlights

- Secure registration and login with hashed passwords
- Professional customer dashboard with balance insights and quick actions
- Deposit, withdraw, and internal transfer workflows
- Searchable transaction history with CSV statement download
- Profile management, password updates, and account deletion
- Admin command center with customer and transaction overview

## Tech Stack

- Python
- Flask
- SQLite
- HTML + Jinja templates
- CSS + Bootstrap 5

## Default Admin Credentials

- Username: `admin`
- Password: `admin123`

## Run Locally

1. Install dependencies:
   `pip install -r requirements.txt`
2. Start the app:
   `python app.py`
3. Open:
   `http://127.0.0.1:5000/`

## Project Structure

- `app.py` - Flask routes, validation, and database logic
- `templates/` - Shared layout plus customer and admin pages
- `static/css/style.css` - Custom design system and responsive styling
- `bank.db` - SQLite database
