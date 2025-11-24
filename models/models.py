from datetime import datetime
from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    student_staff_id = db.Column(db.String(64), nullable=True)
    verified = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(256), nullable=False)
    photo_url = db.Column(db.String(256), nullable=True)
    rating_avg = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Ride(db.Model):
    __tablename__ = 'rides'
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    origin = db.Column(db.String(256))
    destination = db.Column(db.String(256))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    seats = db.Column(db.Integer)
    price = db.Column(db.Float)
    status = db.Column(db.String(32), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'))
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(32), default='pending')
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    seats_booked = db.Column(db.Integer, default=1)


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'))
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ratee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    stars = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'))
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount = db.Column(db.Float)
    status = db.Column(db.String(32), default='pending')
    transaction_id = db.Column(db.String(128), nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)


class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=True)
    reason = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='pending') # pending, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
