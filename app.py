from flask import Flask, render_template, request, redirect, url_for, session
from application.database import db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.sqlite3'
app.config['SECRET_KEY'] = 'your_secret_key_here' 

db.init_app(app)

with app.app_context():
    from application import models 
    db.create_all()
    
    # Automatically Seed the Admin User
    admin_exists = models.User.query.filter_by(role='admin').first()
    if not admin_exists:
        hashed_password = generate_password_hash('admin123') 
        admin_user = models.User(username='admin', password=hashed_password, role='admin')
        db.session.add(admin_user)
        db.session.commit()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

# Student Registration
@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    from application.models import User, StudentProfile

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
        return redirect(url_for('home'))

    return render_template('register_student.html')

# Company Registration
@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    from application.models import User, CompanyProfile

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
        return redirect(url_for('home'))

    return render_template('register_company.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    from application.models import User
    
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
                return redirect(url_for('company_dashboard')) # We will build this next!
            
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
    from application.models import User, PlacementDrive, Application
    
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    student_data = current_user.student_profile
    
    all_drives = PlacementDrive.query.all()

    # Get applications and create the dictionary
    my_applications = Application.query.filter_by(student_id=student_data.id).all()
    applied_drives_dict = {app.drive_id: app.status for app in my_applications}

    # THIS IS THE CRITICAL LINE: Passing 'applied_drives_dict' to the HTML
    return render_template(
        'student_dashboard.html', 
        student=student_data, 
        drives=all_drives, 
        applied_drives=applied_drives_dict 
    )

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    from application.models import StudentProfile, CompanyProfile, PlacementDrive
    
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    total_students = StudentProfile.query.count()
    approved_companies = CompanyProfile.query.filter_by(approval_status='Approved').count()
    pending_companies = CompanyProfile.query.filter_by(approval_status='Pending').count()
    total_drives = PlacementDrive.query.count()

    return render_template(
        'admin_dashboard.html', 
        students=total_students, 
        companies=approved_companies,
        pending=pending_companies,
        drives=total_drives
    )

# --- NEW ADMIN APPROVAL ROUTES ---

@app.route('/admin/manage_companies')
def manage_companies():
    from application.models import CompanyProfile
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    # Fetch all companies to display in the table
    all_companies = CompanyProfile.query.all()
    return render_template('manage_companies.html', companies=all_companies)

@app.route('/admin/approve_company/<int:id>')
def approve_company(id):
    from application.models import CompanyProfile
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    company = CompanyProfile.query.get_or_404(id)
    company.approval_status = 'Approved'
    db.session.commit()
    return redirect(url_for('manage_companies'))

@app.route('/admin/reject_company/<int:id>')
def reject_company(id):
    from application.models import CompanyProfile
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    company = CompanyProfile.query.get_or_404(id)
    company.approval_status = 'Rejected'
    db.session.commit()
    return redirect(url_for('manage_companies'))


# --- COMPANY ROUTES ---

@app.route('/company/dashboard')
def company_dashboard():
    from application.models import User, PlacementDrive # Make sure PlacementDrive is imported!
    
    # SECURITY CHECK
    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))

    # Get the specific company's data
    current_user = User.query.get(session['user_id'])
    company_data = current_user.company_profile
    
    # NEW: Fetch only the drives created by this company
    my_drives = PlacementDrive.query.filter_by(company_id=company_data.id).all()
    
    return render_template('company_dashboard.html', company=company_data, drives=my_drives)

@app.route('/company/create_drive', methods=['GET', 'POST'])
def create_drive():
    from application.models import User, PlacementDrive
    from datetime import datetime
    
    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    company_data = current_user.company_profile

    # Double-check they are approved before allowing them to submit!
    if company_data.approval_status != 'Approved':
        return redirect(url_for('company_dashboard'))

    if request.method == 'POST':
        title = request.form.get('job_title')
        description = request.form.get('job_description')
        eligibility = request.form.get('eligibility')
        deadline_str = request.form.get('deadline') # Comes in as 'YYYY-MM-DD'
        
        # Convert string date to Python datetime object
        deadline_date = datetime.strptime(deadline_str, '%Y-%m-%d').date()

        # Create the Drive in the database
        new_drive = PlacementDrive(
            company_id=company_data.id,
            job_title=title,
            job_description=description,
            eligibility_criteria=eligibility,
            application_deadline=deadline_date,
            status='Approved' # Drives are auto-approved for now, or you could make Admin approve these too!
        )
        db.session.add(new_drive)
        db.session.commit()
        
        return redirect(url_for('company_dashboard'))

    return render_template('create_drive.html')

# --- STUDENT APPLY ROUTE ---

@app.route('/student/apply/<int:drive_id>')
def apply_drive(drive_id):
    from application.models import User, Application # We assume you have an Application model!
    
    # 1. Security Check
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))

    # 2. Get the current student's profile ID
    current_user = User.query.get(session['user_id'])
    student_profile_id = current_user.student_profile.id

    # 3. Check if they already applied to this exact drive
    existing_application = Application.query.filter_by(
        student_id=student_profile_id, 
        drive_id=drive_id
    ).first()

    # 4. If they haven't applied yet, create the application!
    if not existing_application:
        new_app = Application(
            student_id=student_profile_id, 
            drive_id=drive_id, 
            status='Applied' # Status starts as Applied or Pending
        )
        db.session.add(new_app)
        db.session.commit()

    # 5. Send them back to the dashboard
    return redirect(url_for('student_dashboard'))

# --- COMPANY VIEW APPLICANTS ROUTE ---

@app.route('/company/drive/<int:drive_id>/applicants')
def view_applicants(drive_id):
    from application.models import User, PlacementDrive, Application
    
    # 1. Security Check
    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))

    # 2. Get the logged-in company's data
    current_user = User.query.get(session['user_id'])
    company_data = current_user.company_profile
    
    # 3. Fetch the specific drive
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    # SECURITY: Make sure this company actually owns this drive!
    if drive.company_id != company_data.id:
        return redirect(url_for('company_dashboard'))

    # 4. Fetch all applications linked to this specific drive
    applications = Application.query.filter_by(drive_id=drive_id).all()

    # 5. Send the data to the HTML page
    return render_template('view_applicants.html', drive=drive, applications=applications)


# --- COMPANY UPDATE APPLICATION ROUTE ---

@app.route('/company/application/<int:app_id>/update', methods=['POST'])
def update_application_status(app_id):
    from application.models import Application
    
    # Security Check
    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))

    # Get the new status from the form buttons (either 'Accepted' or 'Rejected')
    new_status = request.form.get('status')
    
    # Find the specific application in the database
    application = Application.query.get_or_404(app_id)
    
    # Update it and save!
    application.status = new_status
    db.session.commit()

    # Send the company back to the same applicant list
    return redirect(url_for('view_applicants', drive_id=application.drive_id))

if __name__ == '__main__':
    app.run(debug=True)