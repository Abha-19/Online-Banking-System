import csv
import io
import os
import random
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, flash, make_response, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "banking-app-secret-key")

APP_NAME = "NorthStar Bank"
DATABASE = "bank.db"
STARTING_BALANCE = 5000
MAX_DEPOSIT_AMOUNT = 100000
MIN_NAME_LENGTH = 3
MIN_USERNAME_LENGTH = 4
MIN_PASSWORD_LENGTH = 6


def get_db_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                account_number TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                balance INTEGER NOT NULL DEFAULT 0,
                is_admin INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                amount INTEGER NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_transactions_user_id
            ON transactions(user_id)
            """
        )

        admin = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
        if not admin:
            conn.execute(
                """
                INSERT INTO users (full_name, account_number, username, password, balance, is_admin)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "Administrator",
                    generate_account_number(conn),
                    "admin",
                    generate_password_hash("admin123"),
                    0,
                    1,
                ),
            )


def generate_account_number(conn):
    while True:
        account_number = str(random.randint(1000000000, 9999999999))
        existing = conn.execute(
            "SELECT id FROM users WHERE account_number = ?",
            (account_number,),
        ).fetchone()
        if existing is None:
            return account_number


def format_currency(amount):
    return f"Rs {amount:,.0f}"


def current_timestamp():
    return datetime.now().strftime("%d %b %Y, %I:%M %p")


def parse_amount(raw_amount):
    value = (raw_amount or "").strip()
    if not value.isdigit():
        return None

    amount = int(value)
    if amount <= 0:
        return None
    return amount


def record_transaction(conn, user_id, action, amount, details):
    conn.execute(
        """
        INSERT INTO transactions (user_id, action, amount, details, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, action, amount, details, current_timestamp()),
    )


def get_user_by_id(user_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(admin_only=False, user_only=False):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            user_id = session.get("user_id")
            is_admin = session.get("is_admin") == 1

            if not user_id:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login"))

            if admin_only and not is_admin:
                flash("Admin access only.", "danger")
                return redirect(url_for("login"))

            if user_only and is_admin:
                flash("Please log in with a customer account to access that page.", "warning")
                return redirect(url_for("login"))

            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def get_dashboard_metrics(user_id):
    with get_db_connection() as conn:
        credits = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = ? AND action IN ('Deposit', 'Received')
            """,
            (user_id,),
        ).fetchone()[0]

        debits = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id = ? AND action IN ('Withdraw', 'Transfer')
            """,
            (user_id,),
        ).fetchone()[0]

        transfer_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE user_id = ? AND action = 'Transfer'
            """,
            (user_id,),
        ).fetchone()[0]

        transaction_count = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]

    return {
        "credits": credits,
        "debits": debits,
        "net_flow": credits - debits,
        "transfer_count": transfer_count,
        "transaction_count": transaction_count,
    }


def get_admin_metrics():
    with get_db_connection() as conn:
        total_customers = conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_admin = 0"
        ).fetchone()[0]
        total_balances = conn.execute(
            "SELECT COALESCE(SUM(balance), 0) FROM users WHERE is_admin = 0"
        ).fetchone()[0]
        total_transactions = conn.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]
        active_today = conn.execute(
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE created_at LIKE ?
            """,
            (f"%{datetime.now().strftime('%d %b %Y')}%",),
        ).fetchone()[0]

    return {
        "total_customers": total_customers,
        "total_balances": total_balances,
        "total_transactions": total_transactions,
        "active_today": active_today,
    }


@app.context_processor
def inject_template_helpers():
    current_user = None
    user_id = session.get("user_id")
    if user_id:
        current_user = get_user_by_id(user_id)

    return {
        "app_name": APP_NAME,
        "current_user": current_user,
        "currency": format_currency,
        "is_admin_session": session.get("is_admin") == 1,
        "current_year": datetime.now().year,
    }


@app.route("/")
def home():
    metrics = get_admin_metrics()
    return render_template("index.html", metrics=metrics)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if len(full_name) < MIN_NAME_LENGTH:
            flash(f"Full name must be at least {MIN_NAME_LENGTH} characters.", "danger")
            return redirect(url_for("register"))

        if len(username) < MIN_USERNAME_LENGTH:
            flash(f"Username must be at least {MIN_USERNAME_LENGTH} characters.", "danger")
            return redirect(url_for("register"))

        if len(password) < MIN_PASSWORD_LENGTH:
            flash(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.", "danger")
            return redirect(url_for("register"))

        if username.lower() == "admin":
            flash("That username is reserved.", "danger")
            return redirect(url_for("register"))

        with get_db_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO users (full_name, account_number, username, password, balance, is_admin)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        full_name,
                        generate_account_number(conn),
                        username,
                        generate_password_hash(password),
                        STARTING_BALANCE,
                        0,
                    ),
                )
            except sqlite3.IntegrityError:
                flash("That username is already taken. Please choose another one.", "danger")
                return redirect(url_for("register"))

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["is_admin"] = user["is_admin"]

            flash("Login successful.", "success")
            if user["is_admin"] == 1:
                return redirect(url_for("admin_panel"))
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
@login_required(user_only=True)
def dashboard():
    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (session["user_id"],),
        ).fetchone()

        recent_transactions = conn.execute(
            """
            SELECT * FROM transactions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 6
            """,
            (session["user_id"],),
        ).fetchall()

    metrics = get_dashboard_metrics(session["user_id"])
    return render_template(
        "dashboard.html",
        user=user,
        recent_transactions=recent_transactions,
        metrics=metrics,
    )


@app.route("/profile")
@login_required(user_only=True)
def profile():
    user = get_user_by_id(session["user_id"])
    metrics = get_dashboard_metrics(session["user_id"])
    return render_template("profile.html", user=user, metrics=metrics)


@app.route("/change_password", methods=["GET", "POST"])
@login_required(user_only=True)
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()

            if not check_password_hash(user["password"], current_password):
                flash("Current password is incorrect.", "danger")
                return redirect(url_for("change_password"))

            if len(new_password) < MIN_PASSWORD_LENGTH:
                flash(f"New password must be at least {MIN_PASSWORD_LENGTH} characters.", "danger")
                return redirect(url_for("change_password"))

            if new_password != confirm_password:
                flash("New password and confirmation do not match.", "danger")
                return redirect(url_for("change_password"))

            if current_password == new_password:
                flash("Choose a password that is different from the current one.", "warning")
                return redirect(url_for("change_password"))

            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (generate_password_hash(new_password), session["user_id"]),
            )

        flash("Password changed successfully.", "success")
        return redirect(url_for("profile"))

    return render_template("change_password.html")


@app.route("/deposit", methods=["GET", "POST"])
@login_required(user_only=True)
def deposit():
    if request.method == "POST":
        amount = parse_amount(request.form.get("amount"))
        if amount is None:
            flash("Enter a valid deposit amount.", "danger")
            return redirect(url_for("deposit"))

        if amount > MAX_DEPOSIT_AMOUNT:
            flash(f"Deposit limit exceeded. Maximum allowed is {format_currency(MAX_DEPOSIT_AMOUNT)}.", "danger")
            return redirect(url_for("deposit"))

        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()

            new_balance = user["balance"] + amount
            conn.execute(
                "UPDATE users SET balance = ? WHERE id = ?",
                (new_balance, session["user_id"]),
            )
            record_transaction(conn, session["user_id"], "Deposit", amount, "Funds added to account")

        flash(f"{format_currency(amount)} deposited successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("deposit.html")


@app.route("/withdraw", methods=["GET", "POST"])
@login_required(user_only=True)
def withdraw():
    if request.method == "POST":
        amount = parse_amount(request.form.get("amount"))
        if amount is None:
            flash("Enter a valid withdrawal amount.", "danger")
            return redirect(url_for("withdraw"))

        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()

            if amount > user["balance"]:
                flash("Insufficient balance for this withdrawal.", "danger")
                return redirect(url_for("withdraw"))

            new_balance = user["balance"] - amount
            conn.execute(
                "UPDATE users SET balance = ? WHERE id = ?",
                (new_balance, session["user_id"]),
            )
            record_transaction(conn, session["user_id"], "Withdraw", amount, "Cash withdrawn from account")

        flash(f"{format_currency(amount)} withdrawn successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("withdraw.html")


@app.route("/transfer", methods=["GET", "POST"])
@login_required(user_only=True)
def transfer():
    if request.method == "POST":
        recipient_username = request.form.get("recipient", "").strip()
        amount = parse_amount(request.form.get("amount"))

        if not recipient_username:
            flash("Recipient username is required.", "danger")
            return redirect(url_for("transfer"))

        if amount is None:
            flash("Enter a valid transfer amount.", "danger")
            return redirect(url_for("transfer"))

        with get_db_connection() as conn:
            sender = conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()

            recipient = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (recipient_username,),
            ).fetchone()

            if recipient is None or recipient["is_admin"] == 1:
                flash("Recipient account was not found.", "danger")
                return redirect(url_for("transfer"))

            if sender["username"].lower() == recipient_username.lower():
                flash("You cannot transfer money to your own account.", "danger")
                return redirect(url_for("transfer"))

            if amount > sender["balance"]:
                flash("Insufficient balance for this transfer.", "danger")
                return redirect(url_for("transfer"))

            conn.execute(
                "UPDATE users SET balance = ? WHERE id = ?",
                (sender["balance"] - amount, sender["id"]),
            )
            conn.execute(
                "UPDATE users SET balance = ? WHERE id = ?",
                (recipient["balance"] + amount, recipient["id"]),
            )

            record_transaction(
                conn,
                sender["id"],
                "Transfer",
                amount,
                f"Transferred to @{recipient['username']}",
            )
            record_transaction(
                conn,
                recipient["id"],
                "Received",
                amount,
                f"Received from @{sender['username']}",
            )

        flash(f"{format_currency(amount)} transferred to @{recipient_username} successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("transfer.html")


@app.route("/history")
@login_required(user_only=True)
def history():
    search_query = request.args.get("search", "").strip()

    with get_db_connection() as conn:
        if search_query:
            transactions = conn.execute(
                """
                SELECT * FROM transactions
                WHERE user_id = ?
                AND (action LIKE ? OR details LIKE ? OR created_at LIKE ?)
                ORDER BY id DESC
                """,
                (
                    session["user_id"],
                    f"%{search_query}%",
                    f"%{search_query}%",
                    f"%{search_query}%",
                ),
            ).fetchall()
        else:
            transactions = conn.execute(
                """
                SELECT * FROM transactions
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (session["user_id"],),
            ).fetchall()

    metrics = get_dashboard_metrics(session["user_id"])
    return render_template(
        "history.html",
        transactions=transactions,
        search_query=search_query,
        metrics=metrics,
    )


@app.route("/download_statement")
@login_required(user_only=True)
def download_statement():
    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (session["user_id"],),
        ).fetchone()

        transactions = conn.execute(
            """
            SELECT * FROM transactions
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (session["user_id"],),
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([APP_NAME + " Statement"])
    writer.writerow(["Full Name", user["full_name"]])
    writer.writerow(["Username", user["username"]])
    writer.writerow(["Account Number", user["account_number"]])
    writer.writerow(["Current Balance", format_currency(user["balance"])])
    writer.writerow([])
    writer.writerow(["Action", "Amount", "Details", "Date and Time"])

    for transaction in transactions:
        writer.writerow(
            [
                transaction["action"],
                format_currency(transaction["amount"]),
                transaction["details"],
                transaction["created_at"],
            ]
        )

    response = make_response(output.getvalue())
    filename = f"{user['username']}_statement_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-Type"] = "text/csv"
    return response


@app.route("/delete_account", methods=["POST"])
@login_required(user_only=True)
def delete_account():
    user_id = session["user_id"]

    with get_db_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    session.clear()
    flash("Your account has been deleted successfully.", "info")
    return redirect(url_for("home"))


@app.route("/admin")
@login_required(admin_only=True)
def admin_panel():
    with get_db_connection() as conn:
        users = conn.execute(
            """
            SELECT * FROM users
            WHERE is_admin = 0
            ORDER BY balance DESC, id DESC
            """
        ).fetchall()

        transactions = conn.execute(
            """
            SELECT transactions.*, users.username, users.full_name
            FROM transactions
            JOIN users ON transactions.user_id = users.id
            ORDER BY transactions.id DESC
            LIMIT 20
            """
        ).fetchall()

    return render_template(
        "admin.html",
        users=users,
        transactions=transactions,
        metrics=get_admin_metrics(),
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


create_table()


if __name__ == "__main__":
    app.run(debug=True)
