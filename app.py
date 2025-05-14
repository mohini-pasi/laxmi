from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="laxmifarmhouse"
)
cursor = db.cursor(buffered=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/booking", methods=["GET", "POST"])
def booking():
    message = None
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        members = request.form.get("members")
        farmhouse = request.form.get("farmhouse")
        date = request.form.get("visit_date")
        advance = request.form.get("advance")

        # Check availability
        cursor.execute("SELECT * FROM bookings WHERE farmhouse=%s AND visit_date=%s", (farmhouse, date))
        result = cursor.fetchone()

        if result:
            message = "❌ Selected date is NOT available!"
        else:
            # Insert into database
            cursor.execute(
                "INSERT INTO bookings (name, phone, members, farmhouse, visit_date, advance_payment) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, phone, members, farmhouse, date, advance)
            )
            db.commit()

            # Save to Excel
            df = pd.DataFrame([[name, phone, members, farmhouse, date, advance]],
                              columns=["Name", "Phone", "Members", "Farmhouse", "Date", "Advance"])
            file_path = "bookings.xlsx"
            if os.path.isfile(file_path):
                old_df = pd.read_excel(file_path)
                df = pd.concat([old_df, df], ignore_index=True)

            df.to_excel(file_path, index=False)
            message = "✅ Thank you for booking!"

    return render_template("booking.html", message=message)

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        flash('You must be logged in to access the admin panel.', 'danger')
        return redirect(url_for('admin_login'))

    try:
        cursor.execute("SELECT * FROM bookings")
        bookings = cursor.fetchall()
        return render_template('admin.html', bookings=bookings)
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        return redirect(url_for('home'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Username and password are required!', 'danger')
            return redirect(url_for('admin_login'))

        if username == 'mahesh' and password == 'mahesh123':
            session['admin_logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password!', 'danger')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

# Run server
if __name__ == '__main__':
    app.run(debug=True)

