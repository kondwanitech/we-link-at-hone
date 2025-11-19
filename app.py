from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from models import db, User, LostItem, FoundItem, Notification, Post, Comment, PostLike, CommentReaction
from forms import RegisterForm, AdminCreateStudentForm, ChangePasswordForm
from config import Config
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail = Mail(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def check_password_change():
    if current_user.is_authenticated and current_user.must_change_password:
        allowed_endpoints = ['change_password', 'logout', 'static']
        if request.endpoint not in allowed_endpoints:
            return redirect(url_for('change_password'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def send_email(to, subject, body):
    server = None
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        username = app.config.get('MAIL_USERNAME')
        password = app.config.get('MAIL_PASSWORD', '').replace(' ', '')
        sender = app.config.get('MAIL_DEFAULT_SENDER') or username
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        use_ssl = app.config.get('MAIL_USE_SSL', False)
        if use_ssl:
            server = smtplib.SMTP_SSL(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        else:
            server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
            if app.config.get('MAIL_USE_TLS', True):
                server.starttls()
        
        server.login(username, password)
        server.send_message(msg)
        
        print(f"Email sent successfully to {to}")
        return True
    except Exception as e:
        error_msg = str(e)
        print(f"Email error sending to {to}: {error_msg}")
        if "Username and Password not accepted" in error_msg or "535" in error_msg:
            print("Authentication failed. If using Gmail, please use an App Password instead of your regular password.")
            print("Create App Password at: https://myaccount.google.com/apppasswords")
        elif "Connection refused" in error_msg:
            print("Cannot connect to mail server. Check MAIL_SERVER and MAIL_PORT settings.")
        return False
    finally:
        if server:
            try:
                server.quit()
            except:
                pass

def create_notification(user_id, message):
    notification = Notification(user_id=user_id, message=message)
    db.session.add(notification)
    db.session.commit()

def find_matching_items(item_name, location, item_type='lost'):
    matches = []
    search_table = FoundItem if item_type == 'lost' else LostItem
    
    all_items = search_table.query.filter_by(status='pending').all()
    
    for item in all_items:
        name_match = item_name.lower() in item.item_name.lower() or item.item_name.lower() in item_name.lower()
        location_match = item.location.lower() == location.lower()
        
        if name_match and location_match:
            matches.append(item)
    
    return matches

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin')
def admin_landing():
    return render_template('admin_landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        if User.query.filter_by(student_number=form.student_number.data).first():
            flash('Student number already registered!', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        
        user = User(
            student_number=form.student_number.data, 
            name=form.name.data, 
            email=form.email.data, 
            role='user',
            account_approved=False
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        send_email(form.email.data,
                  'Registration Received - WeLink',
                  f'Welcome to WeLink, {form.name.data}!\n\nYour registration has been received. Your account is pending admin approval.\n\nYou will receive an email confirmation once your account has been approved.')
        
        flash('Registration successful! Your account is pending admin approval. You will receive an email once approved.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=identifier).first()
        if not user:
            user = User.query.filter_by(student_number=identifier).first()
        
        if user and user.check_password(password):
            if user.role == 'admin':
                flash('Please use the admin login page.', 'error')
                return redirect(url_for('admin_login'))
            
            if not user.account_approved:
                flash('Your account is pending admin approval. Please wait for approval.', 'error')
                return redirect(url_for('login'))
            
            login_user(user)
            if user.must_change_password:
                return redirect(url_for('change_password'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('student_login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=identifier).first()
        if not user:
            user = User.query.filter_by(student_number=identifier).first()
        
        if user and user.check_password(password):
            if user.role != 'admin':
                flash('Access denied! Admin credentials required.', 'error')
                return redirect(url_for('admin_login'))
            
            login_user(user)
            if user.must_change_password:
                return redirect(url_for('change_password'))
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'error')
    
    return render_template('admin_login.html')

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect!', 'error')
            return redirect(url_for('change_password'))
        
        current_user.set_password(form.new_password.data)
        current_user.must_change_password = False
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    return render_template('change_password.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    lost_items = LostItem.query.order_by(LostItem.date_created.desc()).all()
    found_items = FoundItem.query.order_by(FoundItem.date_created.desc()).all()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.date_created.desc()).limit(5).all()
    
    return render_template('dashboard.html', lost_items=lost_items, found_items=found_items, notifications=notifications)

@app.route('/report-lost', methods=['GET', 'POST'])
@login_required
def report_lost():
    if request.method == 'POST':
        item_name = request.form.get('item_name')
        category = request.form.get('category')
        color = request.form.get('color')
        model = request.form.get('model')
        size = request.form.get('size')
        description = request.form.get('description')
        date_lost = datetime.strptime(request.form.get('date_lost'), '%Y-%m-%d').date()
        location = request.form.get('location')
        
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{current_user.id}_{datetime.now().timestamp()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename
        
        lost_item = LostItem(
            user_id=current_user.id,
            item_name=item_name,
            category=category,
            color=color,
            model=model,
            size=size,
            description=description,
            date_lost=date_lost,
            location=location,
            image_path=image_path
        )
        db.session.add(lost_item)
        db.session.commit()
        
        send_email(current_user.email, 
                  'Lost Item Reported - WeLink',
                  f'Your lost item "{item_name}" has been reported successfully. We will notify you if someone finds a matching item.')
        
        matching_found_items = find_matching_items(item_name, location, 'lost')
        for found_item in matching_found_items:
            create_notification(current_user.id, 
                f'Potential match found! Someone reported finding a "{found_item.item_name}" at {found_item.location}.')
            create_notification(found_item.user_id,
                f'Potential match! Someone lost a "{item_name}" at {location} that might match your found item.')
            
            send_email(current_user.email,
                'Potential Match Found - WeLink',
                f'Good news! A "{found_item.item_name}" was found at {found_item.location}. This might be your item!')
            send_email(found_item.user.email,
                'Potential Match Found - WeLink',
                f'Someone reported losing a "{item_name}" at {location}. This might match your found item!')
        
        flash('Lost item reported successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('report_lost.html')

@app.route('/submit-found', methods=['GET', 'POST'])
@login_required
def submit_found():
    if request.method == 'POST':
        item_name = request.form.get('item_name')
        category = request.form.get('category')
        color = request.form.get('color')
        model = request.form.get('model')
        size = request.form.get('size')
        description = request.form.get('description')
        date_found = datetime.strptime(request.form.get('date_found'), '%Y-%m-%d').date()
        location = request.form.get('location')
        
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{current_user.id}_{datetime.now().timestamp()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename
        
        found_item = FoundItem(
            user_id=current_user.id,
            item_name=item_name,
            category=category,
            color=color,
            model=model,
            size=size,
            description=description,
            date_found=date_found,
            location=location,
            image_path=image_path
        )
        db.session.add(found_item)
        db.session.commit()
        
        send_email(current_user.email,
                  'Found Item Submitted - WeLink',
                  f'Your found item "{item_name}" has been submitted successfully. Item owners will be notified.')
        
        matching_lost_items = find_matching_items(item_name, location, 'found')
        for lost_item in matching_lost_items:
            create_notification(current_user.id,
                f'Potential match found! Someone reported losing a "{lost_item.item_name}" at {lost_item.location}.')
            create_notification(lost_item.user_id,
                f'Great news! Someone found a "{item_name}" at {location} that might be yours!')
            
            send_email(current_user.email,
                'Potential Match Found - WeLink',
                f'Someone lost a "{lost_item.item_name}" at {lost_item.location}. This might match your found item!')
            send_email(lost_item.user.email,
                'Potential Match Found - WeLink',
                f'Great news! A "{item_name}" was found at {location}. This might be your lost item!')
        
        flash('Found item submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('submit_found.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    pending_approvals = User.query.filter_by(account_approved=False, role='user').all()
    lost_items = LostItem.query.order_by(LostItem.date_created.desc()).all()
    found_items = FoundItem.query.order_by(FoundItem.date_created.desc()).all()
    
    stats = {
        'total_users': len(users),
        'total_lost': len(lost_items),
        'total_found': len(found_items),
        'pending_lost': len([i for i in lost_items if i.status == 'pending']),
        'pending_found': len([i for i in found_items if i.status == 'pending']),
        'pending_approvals': len(pending_approvals)
    }
    
    return render_template('admin_dashboard.html', stats=stats, users=users, lost_items=lost_items, found_items=found_items, pending_approvals=pending_approvals)

@app.route('/admin/approve-student/<int:user_id>', methods=['POST'])
@login_required
def admin_approve_student(user_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    student = User.query.get_or_404(user_id)
    
    if student.role == 'admin':
        flash('Cannot approve admin accounts!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if student.account_approved:
        flash('Account is already approved!', 'info')
        return redirect(url_for('admin_dashboard'))
    
    student.account_approved = True
    db.session.commit()
    
    send_email(student.email,
              'Account Approved - WeLink',
              f'Dear {student.name},\n\nYour WeLink account has been approved by the administrator!\n\nYou can now log in using:\nStudent Number: {student.student_number}\nEmail: {student.email}\n\nWelcome to WeLink - Evelyn Hone College Lost and Found System!')
    
    flash(f'Student {student.name} approved successfully! Confirmation email sent.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject-student/<int:user_id>', methods=['POST'])
@login_required
def admin_reject_student(user_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    student = User.query.get_or_404(user_id)
    
    if student.role == 'admin':
        flash('Cannot reject admin accounts!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if student.account_approved:
        flash('Cannot reject approved accounts!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    send_email(student.email,
              'Registration Not Approved - WeLink',
              f'Dear {student.name},\n\nWe regret to inform you that your WeLink registration was not approved.\n\nPlease contact the administrator for more information.')
    
    db.session.delete(student)
    db.session.commit()
    
    flash(f'Student registration for {student.name} has been rejected and removed.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/send-email/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_send_email(user_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    student = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if not subject or not message:
            flash('Subject and message are required!', 'error')
            return redirect(url_for('admin_send_email', user_id=user_id))
        
        email_sent = send_email(student.email, subject, message)
        
        if email_sent:
            flash(f'Email sent successfully to {student.name}!', 'success')
        else:
            flash(f'Failed to send email to {student.name}. Please check email configuration.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_send_email.html', student=student)

@app.route('/admin/create-student', methods=['GET', 'POST'])
@login_required
def admin_create_student():
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    form = AdminCreateStudentForm()
    
    if form.validate_on_submit():
        if User.query.filter_by(student_number=form.student_number.data).first():
            flash('Student number already exists!', 'error')
            return redirect(url_for('admin_create_student'))
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists!', 'error')
            return redirect(url_for('admin_create_student'))
        
        new_student = User(
            student_number=form.student_number.data,
            name=form.name.data,
            email=form.email.data,
            role='user',
            must_change_password=True,
            account_approved=True
        )
        new_student.set_password(form.temp_password.data)
        db.session.add(new_student)
        db.session.commit()
        
        send_email(form.email.data,
                  'Welcome to WeLink - Evelyn Hone College',
                  f'Your account has been created.\n\nStudent Number: {form.student_number.data}\nTemporary Password: {form.temp_password.data}\n\nYou must change your password upon first login.')
        
        flash(f'Student account created successfully! Temporary password: {form.temp_password.data}', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_create_student.html', form=form)

@app.route('/admin/delete-student/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_student(user_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    student = User.query.get_or_404(user_id)
    
    if student.role == 'admin':
        flash('Cannot delete admin accounts!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {student.name} deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit-student/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_student(user_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    student = User.query.get_or_404(user_id)
    
    if student.role == 'admin':
        flash('Cannot edit admin accounts!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        student_number = request.form.get('student_number')
        name = request.form.get('name')
        email = request.form.get('email')
        reset_password = request.form.get('reset_password')
        
        existing_student = User.query.filter_by(student_number=student_number).first()
        if existing_student and existing_student.id != student.id:
            flash('Student number already exists!', 'error')
            return redirect(url_for('admin_edit_student', user_id=user_id))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != student.id:
            flash('Email already exists!', 'error')
            return redirect(url_for('admin_edit_student', user_id=user_id))
        
        student.student_number = student_number
        student.name = name
        student.email = email
        
        if reset_password:
            student.set_password(reset_password)
            student.must_change_password = True
            send_email(email,
                      'Password Reset - WeLink',
                      f'Your password has been reset by an administrator.\n\nNew Temporary Password: {reset_password}\n\nYou must change your password upon next login.')
        
        db.session.commit()
        flash('Student details updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_edit_student.html', student=student)

@app.route('/admin/update-item/<item_type>/<int:item_id>/<action>', methods=['POST'])
@login_required
def admin_update_item(item_type, item_id, action):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if item_type == 'lost':
        item = LostItem.query.get_or_404(item_id)
    else:
        item = FoundItem.query.get_or_404(item_id)
    
    if action == 'approve':
        item.status = 'approved'
        create_notification(item.user_id, f'Your {item_type} item "{item.item_name}" has been approved!')
    elif action == 'delete':
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    db.session.commit()
    flash(f'Item {action}d successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/mark-returned/<int:item_id>', methods=['POST'])
@login_required
def mark_returned(item_id):
    item = LostItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized!', 'error')
        return redirect(url_for('dashboard'))
    
    item.status = 'returned'
    db.session.commit()
    flash('Item marked as returned!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/mark-claimed/<int:item_id>', methods=['POST'])
@login_required
def mark_claimed(item_id):
    item = FoundItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized!', 'error')
        return redirect(url_for('dashboard'))
    
    item.status = 'claimed'
    db.session.commit()
    flash('Item marked as claimed!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete-lost/<int:item_id>', methods=['POST'])
@login_required
def delete_lost_item(item_id):
    item = LostItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized!', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(item)
    db.session.commit()
    flash('Lost item deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete-found/<int:item_id>', methods=['POST'])
@login_required
def delete_found_item(item_id):
    item = FoundItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorized!', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(item)
    db.session.commit()
    flash('Found item deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/test-email', methods=['GET'])
@login_required
def test_email_config():
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    import smtplib
    mail_password = app.config.get('MAIL_PASSWORD', '')
    diagnostics = {
        'username': app.config.get('MAIL_USERNAME'),
        'sender': app.config.get('MAIL_DEFAULT_SENDER'),
        'server': app.config.get('MAIL_SERVER'),
        'port': app.config.get('MAIL_PORT'),
        'tls': app.config.get('MAIL_USE_TLS'),
        'ssl': app.config.get('MAIL_USE_SSL'),
        'password_set': bool(mail_password),
        'password_length': len(mail_password) if mail_password else 0,
        'has_spaces': ' ' in mail_password if mail_password else False
    }
    
    test_result = "Not tested"
    server = None
    try:
        use_ssl = app.config.get('MAIL_USE_SSL', False)
        if use_ssl:
            server = smtplib.SMTP_SSL(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        else:
            server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
            if app.config.get('MAIL_USE_TLS', True):
                server.starttls()
        
        password = mail_password.replace(' ', '') if mail_password else ''
        server.login(app.config.get('MAIL_USERNAME', ''), password)
        test_result = "✅ Connection successful! Email credentials are working."
    except Exception as e:
        test_result = f"❌ Connection failed: {str(e)}"
    finally:
        if server:
            try:
                server.quit()
            except:
                pass
    
    diagnostics['test_result'] = test_result
    
    return jsonify(diagnostics)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    item_type = request.args.get('type', 'all')
    location = request.args.get('location', '')
    
    lost_items = []
    found_items = []
    
    if item_type in ['all', 'lost']:
        lost_query = LostItem.query
        if query:
            lost_query = lost_query.filter(
                (LostItem.item_name.ilike(f'%{query}%')) | 
                (LostItem.description.ilike(f'%{query}%'))
            )
        if location:
            lost_query = lost_query.filter(LostItem.location.ilike(f'%{location}%'))
        lost_items = lost_query.order_by(LostItem.date_created.desc()).all()
    
    if item_type in ['all', 'found']:
        found_query = FoundItem.query
        if query:
            found_query = found_query.filter(
                (FoundItem.item_name.ilike(f'%{query}%')) | 
                (FoundItem.description.ilike(f'%{query}%'))
            )
        if location:
            found_query = found_query.filter(FoundItem.location.ilike(f'%{location}%'))
        found_items = found_query.order_by(FoundItem.date_created.desc()).all()
    
    return render_template('search_results.html', lost_items=lost_items, found_items=found_items, query=query)

@app.route('/feed')
@login_required
def feed():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    posts = Post.query.order_by(Post.date_created.desc()).all()
    return render_template('feed.html', posts=posts)

@app.route('/feed/create', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content')
    
    if not content or not content.strip():
        flash('Post content cannot be empty!', 'error')
        return redirect(url_for('feed'))
    
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"post_{current_user.id}_{datetime.now().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = filename
    
    post = Post(
        user_id=current_user.id,
        content=content,
        image_path=image_path
    )
    db.session.add(post)
    db.session.commit()
    
    flash('Post created successfully!', 'success')
    return redirect(url_for('feed'))

@app.route('/feed/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    existing_like = PostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({'success': True, 'liked': False, 'likes_count': post.get_likes_count()})
    else:
        like = PostLike(post_id=post_id, user_id=current_user.id)
        db.session.add(like)
        db.session.commit()
        return jsonify({'success': True, 'liked': True, 'likes_count': post.get_likes_count()})

@app.route('/feed/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    
    if not content or not content.strip():
        return jsonify({'success': False, 'message': 'Comment cannot be empty'})
    
    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        content=content
    )
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'user_name': current_user.name,
            'date_created': comment.date_created.strftime('%B %d, %Y at %I:%M %p')
        }
    })

@app.route('/feed/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        flash('You can only delete your own posts!', 'error')
        return redirect(url_for('feed'))
    
    if post.image_path:
        image_file = os.path.join(app.config['UPLOAD_FOLDER'], post.image_path)
        if os.path.exists(image_file):
            os.remove(image_file)
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('feed'))

@app.route('/feed/comment/<int:comment_id>/react', methods=['POST'])
@login_required
def react_to_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    existing_reaction = CommentReaction.query.filter_by(comment_id=comment_id, user_id=current_user.id).first()
    
    if existing_reaction:
        db.session.delete(existing_reaction)
        db.session.commit()
        return jsonify({'success': True, 'reacted': False, 'reactions_count': comment.get_reactions_count()})
    else:
        reaction = CommentReaction(comment_id=comment_id, user_id=current_user.id)
        db.session.add(reaction)
        db.session.commit()
        return jsonify({'success': True, 'reacted': True, 'reactions_count': comment.get_reactions_count()})

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                if current_user.profile_picture:
                    old_file = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_picture)
                    if os.path.exists(old_file):
                        os.remove(old_file)
                
                filename = secure_filename(f"profile_{current_user.id}_{datetime.now().timestamp()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_picture = filename
                db.session.commit()
                flash('Profile picture updated successfully!', 'success')
            else:
                flash('Invalid file type. Please upload an image.', 'error')
        
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(role='admin').first():
            admin = User(
                student_number='ADMIN001',
                name='Administrator',
                email='kondwani605@gmail.com',
                role='admin'
            )
            admin.set_password('2004Aug1&')
            db.session.add(admin)
            db.session.commit()
            print('Default admin account created successfully')
    
    app.run(host='0.0.0.0', port=5000, debug=True)
