import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from functools import wraps
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Get the absolute path of the directory containing this file
basedir = os.path.abspath(os.path.dirname(__file__))

# Create the Flask app instance
app = Flask(__name__, template_folder=os.path.join(basedir, 'templates'))
app.secret_key = "Reddy@2001"  # Needed for flash messages and session

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'photographer_bookings'
}

# Database connection function
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

# Initialize SES client with credentials
aws_access_key_id = 'AKIAXKPUZVMGAN7H24QM'  # Replace with your Access Key ID
aws_secret_access_key = 'iNg+IW8faMyo88x/278q7463OqI6VQSQLqeuGmGg'  # Replace with your Secret Access Key
aws_region_name = 'us-east-1'  # Replace with your AWS region, e.g., 'us-east-1'

ses_client = boto3.client(
    'ses',
    region_name=aws_region_name,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

# Send email function
def send_email(to_email, subject, body):
    try:
        response = ses_client.send_email(
            Source='apurvapeddireddy0904@gmail.com',  # Use a verified email address
            Destination={
                'ToAddresses': [to_email],
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        print(f"Email sent! Message ID: {response['MessageId']}")  # Log the Message ID
        return response
    except ClientError as e:
        print(f"Error sending email: {e.response['Error']['Message']}")  # Log the error message
        return None

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT id, email, password FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                
                if user:
                    user_id, user_email, hashed_password = user
                    if check_password_hash(hashed_password, password):
                        session['user_id'] = user_id
                        return redirect(url_for('home'))
                    else:
                        flash("Invalid email or password", "error")
                else:
                    flash("User not found", "error")
                
                return redirect(url_for('login'))
            except mysql.connector.Error as e:
                print(f"Error: {e}")
                flash("An error occurred during login. Please try again.", "error")
            finally:
                cursor.close()
                connection.close()
        else:
            flash("Unable to connect to the database. Please try again later.", "error")
    
    return render_template('login.html')

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/events")
def events():
    return render_template("events.html")

@app.route("/testimonials")
def testimonials():
    return render_template("testimonials.html")

@app.route("/bookings")
def bookings():
    return render_template("bookings.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Retrieve form data for user signup
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')

        # Check if all required fields are present
        if not all([full_name, email, password, confirm_password, phone]):
            flash('All fields are required.', 'error')
            return render_template('signup.html')

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('signup.html')

        # Hash the password
        hashed_password = generate_password_hash(password)

        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # SQL query to insert data into the users table
                sql = """INSERT INTO users 
                         (full_name, email, password, phone) 
                         VALUES (%s, %s, %s, %s)"""
                values = (full_name, email, hashed_password, phone)

                # Execute the query
                cursor.execute(sql, values)
            connection.commit()

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except Error as e:
            if 'Duplicate entry' in str(e):
                flash('An account with this email already exists.', 'error')
            else:
                flash('An error occurred. Please try again.', 'error')
        finally:
            if connection:
                connection.close()

    return render_template('signup.html')

@app.route("/book", methods=['GET', 'POST'])
def book_event():
    if request.method == 'POST':
        # Retrieve form data for event booking
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        event_type = request.form.get('event_type')
        event_date = request.form.get('event_date')
        guests = request.form.get('guests')
        special_requests = request.form.get('special_requests', '')

        # Validate form inputs
        if not all([full_name, email, phone, event_type, event_date, guests]):
            flash('All fields except special requests are required.', 'error')
            return render_template('book_event.html')

        try:
            connection = get_db_connection()
            if connection is None:
                flash("Database connection failed. Try again later.", 'error')
                return render_template('book_event.html')

            with connection.cursor() as cursor:
                # SQL query to insert data into the event_bookings table
                sql = """INSERT INTO event_bookings 
                         (full_name, email, phone, event_type, event_date, guests, special_requests, status) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')"""
                values = (full_name, email, phone, event_type, event_date, guests, special_requests)

                # Execute the query
                cursor.execute(sql, values)
            connection.commit()

            # Prepare the email messages for the photographer
            photographer_email = "photographer@example.com"  # Replace with the photographer's email
            subject = "New Booking Notification"
            body = f"""New booking received!

**Booking Details:**
- **Customer Name:** {full_name}
- **Customer Email:** {email}
- **Phone:** {phone}
- **Event Type:** {event_type}
- **Event Date:** {event_date}
- **Number of Guests:** {guests}
- **Special Requests:** {special_requests}
"""

            # Send email to the photographer
            photographer_email_response = send_email(photographer_email, subject, body)

            if photographer_email_response:
                flash('Event booked successfully! A notification email has been sent to the photographer.', 'success')
            else:
                flash('Event booked successfully! However, there was an issue sending the notification email to the photographer.', 'warning')

            return render_template('book_event.html')
        except Error as e:
            print(f"Database error: {e}")
            flash('An error occurred while booking. Please try again.', 'error')
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
        finally:
            if connection:
                connection.close()

    return render_template('book_event.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    if conn is None:
        flash("Unable to connect to the database", "error")
        return redirect(url_for('index'))

    try:
        cursor = conn.cursor(dictionary=True)

        # Fetch all event bookings
        cursor.execute(''' 
            SELECT id, full_name, email, event_type, event_date, guests, special_requests, status
            FROM event_bookings
            ORDER BY event_date DESC
        ''')
        
        events = cursor.fetchall()
        
        return render_template('dashboard.html', events=events)
    except Error as e:
        print(f"Error fetching bookings: {e}")
        flash('An error occurred while fetching bookings. Please try again.', 'error')
        return redirect(url_for('index'))
    finally:
        cursor.close()
        conn.close()

@app.route('/confirm_booking/<int:booking_id>')
@login_required
def confirm_booking(booking_id):
    conn = get_db_connection()
    if conn is None:
        flash("Unable to connect to the database", "error")
        return redirect(url_for('dashboard'))

    try:
        cursor = conn.cursor()
        cursor.execute(''' 
            UPDATE event_bookings 
            SET status = 'confirmed' 
            WHERE id = %s
        ''', (booking_id,))
        conn.commit()

        # Fetch the booking details to send the confirmation email
        cursor.execute(''' 
            SELECT full_name, email, event_type, event_date, guests, special_requests 
            FROM event_bookings 
            WHERE id = %s
        ''', (booking_id,))
        booking = cursor.fetchone()
        
        if booking:
            full_name, email, event_type, event_date, guests, special_requests = booking
            subject = "Booking Confirmation"
            body = f"""Dear {full_name},

Your booking has been confirmed!

**Booking Details:**
- **Event Type:** {event_type}
- **Event Date:** {event_date}
- **Number of Guests:** {guests}
- **Special Requests:** {special_requests}

Thank you for choosing our service!

Best regards,
[Your Business Name]
"""

            # Send confirmation email to customer
            send_email(email, subject, body)

        flash('Booking confirmed successfully!', 'success')
    except Error as e:
        print(f"Error confirming booking: {e}")
        flash('An error occurred while confirming the booking. Please try again.', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/decline_booking/<int:booking_id>')
@login_required
def decline_booking(booking_id):
    conn = get_db_connection()
    if conn is None:
        flash("Unable to connect to the database", "error")
        return redirect(url_for('dashboard'))

    try:
        cursor = conn.cursor()
        cursor.execute(''' 
            UPDATE event_bookings 
            SET status = 'declined' 
            WHERE id = %s
        ''', (booking_id,))
        conn.commit()
        
        # Fetch the booking details to send the decline email
        cursor.execute(''' 
            SELECT full_name, email 
            FROM event_bookings 
            WHERE id = %s
        ''', (booking_id,))
        booking = cursor.fetchone()
        
        if booking:
            full_name, email = booking
            subject = "Booking Declined"
            body = f"""Dear {full_name},

We regret to inform you that your booking has been declined.

If you have any questions or wish to make another booking, feel free to contact us.

Best regards,
[Your Business Name]
"""

            # Send decline email to customer
            send_email(email, subject, body)

        flash('Booking declined successfully!', 'success')
    except Error as e:
        print(f"Error declining booking: {e}")
        flash('An error occurred while declining the booking. Please try again.', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/history')
@login_required
def history():
    conn = get_db_connection()
    if conn is None:
        flash("Unable to connect to the database", "error")
        return redirect(url_for('index'))

    try:
        cursor = conn.cursor(dictionary=True)

        # Fetch all event bookings for the logged-in user
        user_id = session['user_id']
        cursor.execute(''' 
            SELECT full_name, email, phone, event_type, event_date, guests, special_requests, status
            FROM event_bookings
            WHERE email = (SELECT email FROM users WHERE id = %s)
            ORDER BY event_date DESC
        ''', (user_id,))
        
        events = cursor.fetchall()
        
        return render_template('history.html', events=events)
    except Error as e:
        print(f"Error fetching history: {e}")
        flash('An error occurred while fetching booking history. Please try again.', 'error')
        return redirect(url_for('index'))
    finally:
        cursor.close()
        conn.close()

@app.context_processor
def utility_processor():
    def now():
        return datetime.now()
    return dict(now=now)

if __name__ == "__main__":
    app.run(debug=True)
