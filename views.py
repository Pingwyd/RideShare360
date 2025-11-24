from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, current_app
from flask_login import login_required, current_user
from .extensions import db
from .models.models import User, Ride, Booking, Message, Payment, Rating, Report
from datetime import datetime
import os
from werkzeug.utils import secure_filename

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    my_rides = Ride.query.filter_by(driver_id=current_user.id).all()
    my_bookings = Booking.query.filter_by(rider_id=current_user.id).all()
    return render_template('dashboard.html', my_rides=my_rides, my_bookings=my_bookings)

@main_bp.route('/rides')
def rides():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date_str = request.args.get('date')
    
    query = Ride.query.filter(Ride.status == 'open')
    
    if origin:
        query = query.filter(Ride.origin.ilike(f'%{origin}%'))
    if destination:
        query = query.filter(Ride.destination.ilike(f'%{destination}%'))
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(Ride.date == date_obj)
        except ValueError:
            pass
            
    rides = query.order_by(Ride.date, Ride.time).all()
    return render_template('rides.html', rides=rides)

@main_bp.route('/rides/create', methods=['GET', 'POST'])
@login_required
def create_ride():
    if not current_user.verified:
        flash('You must be verified to create a ride.', 'warning')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        seats = request.form.get('seats')
        price = request.form.get('price')
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            
            new_ride = Ride(
                driver_id=current_user.id,
                origin=origin,
                destination=destination,
                date=date_obj,
                time=time_obj,
                seats=int(seats),
                price=float(price)
            )
            db.session.add(new_ride)
            db.session.commit()
            flash('Ride created successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            
    return render_template('create_ride.html')

@main_bp.route('/rides/<int:ride_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.driver_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        ride.origin = request.form.get('origin')
        ride.destination = request.form.get('destination')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        ride.seats = int(request.form.get('seats'))
        ride.price = float(request.form.get('price'))
        
        try:
            ride.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            ride.time = datetime.strptime(time_str, '%H:%M:%S').time() if len(time_str) == 8 else datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return render_template('edit_ride.html', ride=ride)

        db.session.commit()
        flash('Ride updated successfully.', 'success')
        return redirect(url_for('main.ride_details', ride_id=ride.id))
        
    return render_template('edit_ride.html', ride=ride)

@main_bp.route('/rides/<int:ride_id>/delete', methods=['POST'])
@login_required
def delete_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.driver_id != current_user.id:
        abort(403)
    
    # Delete associated bookings, messages, etc. (Cascade delete would be better in models)
    Booking.query.filter_by(ride_id=ride.id).delete()
    Message.query.filter_by(ride_id=ride.id).delete()
    
    db.session.delete(ride)
    db.session.commit()
    flash('Ride deleted.', 'success')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/rides/<int:ride_id>')
@login_required
def ride_details(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    driver = User.query.get(ride.driver_id)
    booking = Booking.query.filter_by(ride_id=ride_id, rider_id=current_user.id).first()
    payment = None
    if booking:
        payment = Payment.query.filter_by(ride_id=ride_id, payer_id=current_user.id).first()
        
    # For driver: get all bookings
    driver_bookings = []
    if ride.driver_id == current_user.id:
        driver_bookings = Booking.query.filter_by(ride_id=ride_id).all()
        
    return render_template('ride_details.html', ride=ride, driver=driver, booking=booking, payment=payment, driver_bookings=driver_bookings)

@main_bp.route('/rides/<int:ride_id>/book', methods=['POST'])
@login_required
def book_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.driver_id == current_user.id:
        flash('You cannot book your own ride.', 'warning')
        return redirect(url_for('main.ride_details', ride_id=ride_id))
        
    if ride.seats <= 0:
        flash('No seats available.', 'danger')
        return redirect(url_for('main.ride_details', ride_id=ride_id))

    existing_booking = Booking.query.filter_by(ride_id=ride_id, rider_id=current_user.id).first()
    if existing_booking:
        flash('You have already booked this ride.', 'info')
        return redirect(url_for('main.ride_details', ride_id=ride_id))

    booking = Booking(ride_id=ride_id, rider_id=current_user.id, status='pending')
    db.session.add(booking)
    db.session.commit()
    flash('Booking requested!', 'success')
    return redirect(url_for('main.ride_details', ride_id=ride_id))

@main_bp.route('/bookings/<int:booking_id>/approve')
@login_required
def approve_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    ride = Ride.query.get(booking.ride_id)
    if ride.driver_id != current_user.id:
        abort(403)
        
    booking.status = 'approved'
    db.session.commit()
    flash('Booking approved. Rider can now pay.', 'success')
    return redirect(url_for('main.ride_details', ride_id=ride.id))

@main_bp.route('/bookings/<int:booking_id>/reject')
@login_required
def reject_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    ride = Ride.query.get(booking.ride_id)
    if ride.driver_id != current_user.id:
        abort(403)
        
    booking.status = 'rejected'
    db.session.commit()
    flash('Booking rejected.', 'info')
    return redirect(url_for('main.ride_details', ride_id=ride.id))

@main_bp.route('/bookings/<int:booking_id>/pay', methods=['POST'])
@login_required
def pay_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.rider_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if booking.status != 'approved':
        flash('Booking must be approved by driver before payment.', 'warning')
        return redirect(url_for('main.ride_details', ride_id=booking.ride_id))
        
    ride = Ride.query.get(booking.ride_id)
    
    # Simulate payment
    payment = Payment(
        ride_id=ride.id,
        payer_id=current_user.id,
        amount=ride.price,
        status='completed',
        transaction_id=f'TXN-{datetime.utcnow().timestamp()}',
        paid_at=datetime.utcnow()
    )
    
    booking.status = 'confirmed'
    ride.seats -= booking.seats_booked # Deduct seats
    db.session.add(payment)
    db.session.commit()
    
    flash('Payment successful! Booking confirmed.', 'success')
    return redirect(url_for('main.ride_details', ride_id=ride.id))

@main_bp.route('/rides/<int:ride_id>/rate/<int:user_id>', methods=['GET', 'POST'])
@login_required
def rate_user(ride_id, user_id):
    ride = Ride.query.get_or_404(ride_id)
    ratee = User.query.get_or_404(user_id)
    
    # Verify rater was part of the ride
    is_driver = ride.driver_id == current_user.id
    is_rider = Booking.query.filter_by(ride_id=ride_id, rider_id=current_user.id, status='confirmed').first() is not None
    
    if not (is_driver or is_rider):
        flash('You cannot rate this user.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        stars = int(request.form.get('stars'))
        comment = request.form.get('comment')
        
        rating = Rating(
            ride_id=ride_id,
            rater_id=current_user.id,
            ratee_id=user_id,
            stars=stars,
            comment=comment
        )
        db.session.add(rating)
        
        # Update average rating
        ratings = Rating.query.filter_by(ratee_id=user_id).all()
        total_stars = sum(r.stars for r in ratings) + stars
        ratee.rating_avg = total_stars / (len(ratings) + 1)
        
        db.session.commit()
        flash('Rating submitted!', 'success')
        return redirect(url_for('main.ride_details', ride_id=ride_id))
        
    return render_template('rate_user.html', user=ratee, ride=ride)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename != '':
                filename = secure_filename(file.filename)
                # Ensure upload directory exists
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                current_user.photo_url = url_for('static', filename='uploads/' + filename)
                db.session.commit()
                flash('Profile photo updated.', 'success')
        
        # Handle other profile updates if needed (e.g. phone number)
        
        return redirect(url_for('main.profile'))
        
    return render_template('profile.html')

@main_bp.route('/calculator')
def calculator():
    return render_template('calculator.html')

@main_bp.route('/admin')
@login_required
def admin_dashboard():
    # Simple check for admin (could be a role field or specific email)
    if current_user.email != 'admin@covenant.edu.ng': # Example admin check
         # In a real app, use a role field
         pass 
         
    pending_users = User.query.filter_by(verified=False).all()
    all_users = User.query.all()
    all_rides = Ride.query.all()
    reports = Report.query.filter_by(status='pending').all()
    return render_template('admin.html', pending_users=pending_users, all_users=all_users, all_rides=all_rides, reports=reports)

@main_bp.route('/admin/verify/<int:user_id>')
@login_required
def verify_user(user_id):
    # Add admin check here
    user = User.query.get_or_404(user_id)
    user.verified = True
    db.session.commit()
    flash(f'User {user.name} verified.', 'success')
    return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/bookings/<int:booking_id>/receipt')
@login_required
def receipt(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    payment = Payment.query.filter_by(ride_id=booking.ride_id, payer_id=booking.rider_id).first()
    
    if not payment:
        flash('No payment found for this booking.', 'warning')
        return redirect(url_for('main.dashboard'))
        
    ride = Ride.query.get(booking.ride_id)
    driver = User.query.get(ride.driver_id)
    
    return render_template('receipt.html', booking=booking, payment=payment, ride=ride, driver=driver)

@main_bp.route('/rides/<int:ride_id>/complete', methods=['POST'])
@login_required
def complete_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.driver_id != current_user.id:
        abort(403)
        
    ride.status = 'completed'
    db.session.commit()
    flash('Ride marked as completed.', 'success')
    return redirect(url_for('main.ride_details', ride_id=ride.id))

@main_bp.route('/rides/<int:ride_id>/cancel', methods=['POST'])
@login_required
def cancel_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    if ride.driver_id != current_user.id:
        abort(403)
        
    ride.status = 'cancelled'
    # Logic to refund bookings could go here
    db.session.commit()
    flash('Ride cancelled.', 'warning')
    return redirect(url_for('main.ride_details', ride_id=ride.id))

@main_bp.route('/report/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def report_user(user_id):
    reported_user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        reason = request.form.get('reason')
        description = request.form.get('description')
        
        report = Report(
            reporter_id=current_user.id,
            reported_user_id=user_id,
            reason=reason,
            description=description
        )
        db.session.add(report)
        db.session.commit()
        flash('Report submitted successfully.', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('report.html')

@main_bp.route('/report/ride/<int:ride_id>', methods=['GET', 'POST'])
@login_required
def report_ride(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    
    if request.method == 'POST':
        reason = request.form.get('reason')
        description = request.form.get('description')
        
        report = Report(
            reporter_id=current_user.id,
            ride_id=ride_id,
            reason=reason,
            description=description
        )
        db.session.add(report)
        db.session.commit()
        flash('Report submitted successfully.', 'success')
        return redirect(url_for('main.ride_details', ride_id=ride_id))
        
    return render_template('report.html')

