from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Import the db instance and ALL models from your application folder
from application.database import db
from application.models import User, StudentProfile, CompanyProfile, PlacementDrive, Application

app = Flask(__name__)
app.secret_key = "student_career_initiative_secret_2026"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 1. Initialize DB correctly (ONLY ONCE)
db.init_app(app)

# 2. Setup Logic (Admin Creation)
with app.app_context():
    db.create_all()  # Creates tables based on models.py
    
    # Check if admin exists using the imported User model
    admin_user = User.query.filter_by(role='admin').first()
    
    if not admin_user:
        new_admin = User(
            username='Ashwin', 
            password=generate_password_hash('ashwin123'), 
            role='admin'
        )
        db.session.add(new_admin)
        db.session.commit()
        print("Admin created successfully!")
    else:
        # Sync credentials if you change them in the code
        admin_user.username = 'Ashwin'
        admin_user.password = generate_password_hash('ashwin123')
        db.session.commit()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

# Student Registration
@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        form_username = request.form.get('username')
        form_password = request.form.get('password')
        form_fullname = request.form.get('full_name')
        form_roll = request.form.get('roll_number')

        hashed_password = generate_password_hash(form_password)
        new_user = User(username=form_username, password=hashed_password, role='student')
        db.session.add(new_user)
        db.session.commit()

        new_student_profile = StudentProfile(
            user_id=new_user.id, 
            full_name=form_fullname, 
            roll_number=form_roll
        )
        db.session.add(new_student_profile)
        db.session.commit() 
        return redirect(url_for('login'))

    return render_template('register_student.html')

# Company Registration
@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        form_username = request.form.get('username')
        form_password = request.form.get('password')
        form_company_name = request.form.get('company_name')
        form_hr_contact = request.form.get('hr_contact')
        form_website = request.form.get('website')

        hashed_password = generate_password_hash(form_password)
        new_user = User(username=form_username, password=hashed_password, role='company')
        db.session.add(new_user)
        db.session.commit()

        new_company_profile = CompanyProfile(
            user_id=new_user.id, 
            company_name=form_company_name, 
            hr_contact=form_hr_contact,
            website=form_website
        )
        db.session.add(new_company_profile)
        db.session.commit() 
        return redirect(url_for('login'))

    return render_template('register_company.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form_username = request.form.get('username')
        form_password = request.form.get('password')

        user = User.query.filter_by(username=form_username).first()

        if user and check_password_hash(user.password, form_password):
            session['user_id'] = user.id
            session['role'] = user.role
            
            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'company':
                return redirect(url_for('company_dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password.")

    return render_template('login.html')

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Student Dashboard
@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    student_data = current_user.student_profile
    all_drives = PlacementDrive.query.all()

    my_applications = Application.query.filter_by(student_id=student_data.id).all()
    applied_drives_dict = {app.drive_id: app.status for app in my_applications}

    return render_template(
        'student_dashboard.html', 
        student=student_data, 
        drives=all_drives, 
        applied_drives=applied_drives_dict 
    )

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    companies = CompanyProfile.query.all()
    students = StudentProfile.query.all()
    drives = PlacementDrive.query.all()

    return render_template(
        'admin_dashboard.html', 
        companies=companies, 
        students=students, 
        drives=drives
    )

# --- ADMIN ACTIONS ---

@app.route('/admin/approve_company/<int:id>', methods=['POST'])
def approve_company(id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    company = CompanyProfile.query.get_or_404(id)
    company.approval_status = 'Approved'
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_company/<int:id>', methods=['POST'])
def reject_company(id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    company = CompanyProfile.query.get_or_404(id)
    company.approval_status = 'Rejected'
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# --- COMPANY ROUTES ---

@app.route('/company/dashboard')
def company_dashboard():
    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    company_data = current_user.company_profile
    my_drives = PlacementDrive.query.filter_by(company_id=company_data.id).all()
    
    return render_template('company_dashboard.html', company=company_data, drives=my_drives)

@app.route('/company/create_drive', methods=['GET', 'POST'])
def create_drive():
    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    company_data = current_user.company_profile

    if company_data.approval_status != 'Approved':
        return redirect(url_for('company_dashboard'))

    if request.method == 'POST':
        title = request.form.get('job_title')
        description = request.form.get('job_description')
        eligibility = request.form.get('eligibility')
        deadline_str = request.form.get('deadline')
        
        deadline_date = datetime.strptime(deadline_str, '%Y-%m-%d').date()

        new_drive = PlacementDrive(
            company_id=company_data.id,
            job_title=title,
            job_description=description,
            eligibility_criteria=eligibility,
            application_deadline=deadline_date
        )
        db.session.add(new_drive)
        db.session.commit()
        return redirect(url_for('company_dashboard'))

    return render_template('create_drive.html')

# --- APPLICANT MANAGEMENT ---

@app.route('/student/apply/<int:drive_id>')
def apply_drive(drive_id):
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    student_profile_id = current_user.student_profile.id

    existing_application = Application.query.filter_by(
        student_id=student_profile_id, 
        drive_id=drive_id
    ).first()

    if not existing_application:
        new_app = Application(student_id=student_profile_id, drive_id=drive_id)
        db.session.add(new_app)
        db.session.commit()

    return redirect(url_for('student_dashboard'))

@app.route('/company/drive/<int:drive_id>/applicants')
def view_applicants(drive_id):
    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    if drive.company_id != current_user.company_profile.id:
        return redirect(url_for('company_dashboard'))

    applications = Application.query.filter_by(drive_id=drive_id).all()
    return render_template('view_applicants.html', drive=drive, applications=applications)

@app.route('/company/application/<int:app_id>/update', methods=['POST'])
def update_application_status(app_id):
    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))

    new_status = request.form.get('status')
    application = Application.query.get_or_404(app_id)
    application.status = new_status
    db.session.commit()

    return redirect(url_for('view_applicants', drive_id=application.drive_id))

if __name__ == '__main__':
    app.run(debug=True)