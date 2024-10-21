// server.js
const express = require('express');
const bodyParser = require('body-parser');
const mysql = require('mysql');
const path = require('path');
const app = express();

app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

const db = mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: 'password',
    database: 'your_database'
});

db.connect(err => {
    if (err) throw err;
    console.log('Connected to database');
});

app.post('/register', (req, res) => {
    const { full_name, email, phone_number, address, event_type, event_date, number_of_guests, special_requests } = req.body;

    const registrationQuery = `
        INSERT INTO event_registration (full_name, email, phone_number, address, event_type, event_date, number_of_guests, special_requests)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `;

    db.query(registrationQuery, [full_name, email, phone_number, address, event_type, event_date, number_of_guests, special_requests], (err, result) => {
        if (err) {
            return res.json({ success: false, message: err.message });
        }

        const registrationId = result.insertId;

        const bookingQuery = `
            INSERT INTO event_booking (registration_id, status, payment_status, total_amount)
            VALUES (?, 'pending', 'unpaid', 0.00)
        `;

        db.query(bookingQuery, [registrationId], (err, result) => {
            if (err) {
                return res.json({ success: false, message: err.message });
            }

            res.json({ success: true });
        });
    });
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});