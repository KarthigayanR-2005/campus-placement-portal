# 🎓 Campus Placement Portal

A full-stack, role-based web application designed to streamline the university campus recruitment process. This portal connects Institute Administrators, Hiring Companies, and Students in a single unified platform.

## 🌟 Key Features

### Role-Based Access Control
* **Admin:** Acts as the gatekeeper. Approves or rejects company registrations to ensure portal security and quality.
* **Company:** Can register (pending admin approval), post placement drives, view student applications, and update candidate statuses (Accept/Reject).
* **Student:** Can register, view approved placement drives, apply for roles, and track their application status in real-time.

### Dynamic State Management
* **Real-time Application Tracking:** When a student applies for a drive, the company's dashboard updates instantly. 
* **Interactive Feedback:** When a company makes a hiring decision, the student's dashboard dynamically updates to reflect their new status (e.g., "🎉 You're Hired!").
* **Gatekeeper Protocol:** Unapproved companies are restricted to a pending dashboard until cleared by the administrator.

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Database:** SQLite, Flask-SQLAlchemy
* **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2 Templating
* **Security:** Werkzeug Password Hashing

## 🚀 Installation and Setup

To run this project locally on your machine, follow these steps:

1. **Clone the repository:**

   Bash - git clone [https://github.com/KarthigayanR-2005/campus-placement-portal.git](https://github.com/KarthigayanR-2005/campus-placement-portal.git)

   go to the present directory

   Bash - cd campus-placement-portal

2. **Install Dependencies:**
   Ensure you have Python installed, then run the following command to install the required libraries:

   Bash - pip install flask flask-sqlalchemy werkzeug


3. **Run the Application:**
   Bash - python app.py

   Note: If you have multiple Python versions installed and the above fails, try:
         python3 app.py or python -m flask run

4. **Access the Portal:**

   Open your browser and navigate to: http://127.0.0.1:5000