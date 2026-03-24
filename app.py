from flask import Flask,render_template,request,redirect,url_for,flash,session,abort,jsonify
import mysql.connector
from functools import wraps
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash, check_password_hash
from models import db,User,Course,Enrollment

app=Flask(__name__)

# conn= mysql.connector.connect(
#     host="localhost",
#     user="lms_user",
#     password="lms_password",
#     database="lms_db"
# )

# cursor=conn.cursor()
print("connected to lms database")

app.config['SECRET_KEY'] = 'LMS'


app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql+mysqlconnector://lms_user:lms_password@localhost/lms_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 3600


db.init_app(app)


def api_login_required(f):

    """API: return 401 JSON if not logged in."""
    @wraps(f)

    def decorated_function(*args, **kwargs):

        if not session.get('user_id'):

            return jsonify({

                'status': 'error',

                'message': 'Login required'

            }), 401


        return f(*args, **kwargs)

    return decorated_function


def api_role_required(role):

    """API: return 403 JSON if wrong role."""
    
    def decorator(f):
        @wraps(f)

        def decorated_function(*args, **kwargs):

            if not session.get('user_id'):

                return jsonify({

                    'status': 'error',

                    'message': 'Login required'

                }), 401

            if session.get('role') != role:

                return jsonify({

                    'status': 'error',

                    'message': 'Access denied'

                }), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '')


        if not username or not password:
            flash('username and password are required', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password,password):
            flash('Invalid username or password', 'error')
            return render_template('login.html')   # ✅ stop execution

        # ✅ only runs if login is valid
        session['user_id'] = user.id
        session['role'] = user.role
        session['username'] = user.username
        session.permanent = True

        if user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        return redirect(url_for('student_dashboard'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You Have been logged out','success')
    return redirect(url_for('home'))

def login_required(f):

    """Decorator: redirect to login if user not in session."""

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if not session.get('user_id'):

            flash('Please log in to continue.', 'error')

            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function


def role_required(role):

    """Decorator: abort 403 if session role does not match."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                flash('Please log in to continue.', 'error')
                return redirect(url_for('login'))
            if session.get('role') != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/student/student_dashboard',methods=['GET','POST'])
@login_required
@role_required('student')
def student_dashboard():
    return render_template('student_dashboard.html')


@app.route('/teacher/teacher_dashboard',methods=['GET','POST'])
@login_required
@role_required('teacher')
def teacher_dashboard():
    return render_template('teacher_dashboard.html')



@app.route('/users')
@login_required
@role_required('student')
def list_users():
    users= User.query.all()
    return render_template('user_list.html',users=users)


@app.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('student')
def edit_user(id):

    user = User.query.get_or_404(id)

    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip()
        password = (request.form.get('password') or '').strip()
        role = (request.form.get('role') or '').strip()

        #backend validation
        if not username:
            flash('Username is required','error')
            return render_template('user_edit.html',user=user)
        if not email:
            flash('Email is required','error')
            return render_template('user_edit.html',user=user)
        
        if '@' not in email:
            flash('Provide a valid email','error') 
            return render_template('user_edit.html',user=user)
        
        if not password:
            flash('Password is required','error')
            return render_template('user_edit.html',user=user)
        
        if role not in ('student','teacher'):
            flash('Please select a valid role','error')
            return render_template('user_edit.html',user=user)
        
        existing_user = User.query.filter_by(username=username).first()

        if existing_user and existing_user.id != user.id:
            flash('Username already exist','error') 
            return render_template('user_edit.html', user=user)
        
        existing_email = User.query.filter_by(email=email).first()

        if existing_email and existing_email.id != user.id:
            flash('email already exist','error') 
            return render_template('user_edit.html', user=user)
                
        try:

            user.username=username
            user.email=email
            user.password=generate_password_hash(password)
            user.role=role

            db.session.commit()
            flash('User updated successfully','success')
            return redirect(url_for('list_users'))

        except Exception:
            db.session.rollback()
            flash('Something went wrong,Please try again','error')
            return render_template('user_edit.html', user=user)

    return render_template('user_edit.html', user=user)

@app.route('/user/<int:id>')
@login_required
@role_required('student')
def user_detail(id):
    user=User.query.get_or_404(id)
    return render_template('user_detail.html',user=user)

@app.route('/user/delete/<int:id>')
@login_required
@role_required('student')
def delete_user(id):
    user=User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('list_users'))


# @app.route('/course/create',methods=['GET', 'POST'])
# def course_create():
#     if request.method == 'POST':
#         title=request.form['title']
#         description=request.form.get('description', '')
#         teacher_id=request.form['teacher_id']

#         teachers = Teacher.query.all()
#         course=Course(title=title,description=description,teacher_id=int(teacher_id))
#         db.session.add(course)
#         db.session.commit()

#         return redirect(url_for('list_courses'))
#     teachers=User.query.filter_by(role='teacher').all()
#     return render_template('course_form.html',teachers=teachers)




@app.route('/course/create', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def course_create():

    if request.method == 'POST':

        title = (request.form.get('title') or '').strip()
        description = (request.form.get('description') or '').strip()
        teacher_id_raw = (request.form.get('teacher_id') or '').strip()

        # ✅ validation
        if not title:
            flash('Course title is required','error')
            teachers = User.query.filter_by(role='teacher').all()
            return render_template('course_form.html', teachers=teachers)

        if not teacher_id_raw:
            flash('Please select a teacher','error')
            teachers = User.query.filter_by(role='teacher').all()
            return render_template('course_form.html', teachers=teachers)

        # ✅ FIX: properly assign teacher_id
        try:
            teacher_id = int(teacher_id_raw)
        except ValueError:
            flash('Invalid teacher id','error')
            teachers = User.query.filter_by(role='teacher').all()
            return render_template('course_form.html', teachers=teachers)

        # ✅ FIX: check teacher properly
        teacher = User.query.filter_by(id=teacher_id, role='teacher').first()
        if not teacher:
            flash('Invalid teacher selected','error')
            teachers = User.query.filter_by(role='teacher').all()
            return render_template('course_form.html', teachers=teachers)

        # ✅ save
        try:
            course = Course(
                title=title,   # IMPORTANT (not title)
                description=description,
                teacher_id=teacher_id
            )

            db.session.add(course)
            db.session.commit()
            flash('Course created successfully','success')
            return redirect(url_for('list_courses'))

        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Something went wrong','error')
            teachers = User.query.filter_by(role='teacher').all()
            return render_template('course_form.html', teachers=teachers)

    teachers = User.query.filter_by(role='teacher').all()
    return render_template('course_form.html', teachers=teachers)


@app.route('/courses')
@login_required
def list_courses():
    courses= Course.query.all()
    return render_template('course_list.html', courses=courses)


@app.route('/course/<int:id>')
@login_required
def course_detail(id):
    course=Course.query.get_or_404(id)
    user_enrollment=None

    if session.get('role')=='student' and session.get('user_id'):
        user_enrollment=Enrollment.query.filter_by(user_id=session['user_id'],course_id=id).first()
    return render_template('course_detail.html',course=course,user_enrollment=user_enrollment)



@app.route('/course/<int:id>/enroll', methods=['POST'])
@login_required
@role_required('student')

def enroll_in_course(id):

    """Student clicks Enroll -> status PENDING."""


    course = Course.query.get_or_404(id)
    user_id = session.get('user_id')
    existing = Enrollment.query.filter_by(
        user_id=user_id,
        course_id=id
    ).first()

    if existing:
        flash('You have already requested enrollment or are enrolled.', 'error')
        return redirect(url_for('course_detail', id=id))

    enrollment = Enrollment(
        user_id=user_id,
        course_id=id,
        status='pending'

    )


    db.session.add(enrollment)
    db.session.commit()
    flash('Enrollment requested. Waiting for teacher approval.', 'success')
    return redirect(url_for('course_detail', id=id))


@app.route('/my-enrollments')
@login_required
@role_required('student')

def my_enrollments():

    """Student: view my enrollments."""
    user_id = session.get('user_id')
    enrollments = Enrollment.query.filter_by(
        user_id=user_id).order_by(Enrollment.created_at.desc()).all()

    return render_template(
        'my_enrollments.html',
        enrollments=enrollments)


@app.route('/course/<int:id>/enrollments')
@login_required
@role_required('teacher')
def course_enrollments(id):

    """Teacher: view enrollments for their course."""


    course = Course.query.get_or_404(id)


    if course.teacher_id != session.get('user_id'):
        abort(403)


    enrollments = Enrollment.query.filter_by(course_id=id).order_by(Enrollment.created_at.desc()).all()

    return render_template('course_enrollments.html',course=course,enrollments=enrollments)



@app.route('/enrollment/<int:id>/approve', methods=['POST'])
@login_required
@role_required('teacher')
def approve_enrollment(id):

    """Teacher approves -> ENROLLED."""

    enrollment = Enrollment.query.get_or_404(id)
    course = Course.query.get_or_404(enrollment.course_id)


    if course.teacher_id != session.get('user_id'):
        abort(403)


    if enrollment.status != 'pending':
        flash('Only pending enrollments can be approved.', 'error')
        return redirect(url_for('course_enrollments', id=course.id))

    enrollment.status = 'enrolled'

    db.session.commit()

    flash('Enrollment approved.', 'success')
    return redirect(url_for('course_enrollments', id=course.id))




@app.route('/enrollment/<int:id>/reject', methods=['POST'])
@login_required
@role_required('teacher')

def reject_enrollment(id):

    """Teacher rejects -> REJECTED (permanent)."""

    enrollment = Enrollment.query.get_or_404(id)

    course = Course.query.get_or_404(enrollment.course_id)


    if course.teacher_id != session.get('user_id'):
        abort(403)


    if enrollment.status != 'pending':

        flash('Only pending enrollments can be rejected.', 'error')

        return redirect(url_for('course_enrollments', id=course.id))


    enrollment.status = 'rejected'


    db.session.commit()

    flash('Enrollment rejected.', 'success')

    return redirect(url_for('course_enrollments', id=course.id))



@app.route('/course/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def course_edit(id):

    course = Course.query.get_or_404(id)
    teachers = User.query.filter_by(role='teacher').all()

    if request.method == 'POST':

        title = (request.form.get('title') or '').strip()
        description = (request.form.get('description') or '').strip()
        teacher_id_raw = (request.form.get('teacher_id') or '').strip()

        # ✅ validation
        if not title:
            flash('Course title is required','error')
            return render_template('course_edit.html', course=course, teachers=teachers)

        if not teacher_id_raw:
            flash('Please select a teacher','error')
            return render_template('course_edit.html', course=course, teachers=teachers)

        try:
            teacher_id = int(teacher_id_raw)
        except ValueError:
            flash('Invalid teacher id','error')
            return render_template('course_edit.html', course=course, teachers=teachers)

        # ✅ check teacher exists
        teacher = User.query.filter_by(id=teacher_id, role='teacher').first()
        if not teacher:
            flash('Invalid teacher selected','error')
            return render_template('course_edit.html', course=course, teachers=teachers)

        try:
            # ✅ FIX: use "name" not "title"
            course.name = title
            course.description = description
            course.teacher_id = teacher_id

            db.session.commit()
            flash('Course updated successfully','success')
            return redirect(url_for('list_courses'))

        except Exception as e:
            print(e)
            db.session.rollback()
            flash('Something went wrong','error')
            return render_template('course_edit.html', course=course, teachers=teachers)

    return render_template('course_edit.html', course=course, teachers=teachers)

@app.route('/course/delete/<int:id>')
@login_required
@role_required('teacher')
def course_delete(id):
    course = Course.query.get_or_404(id)
    db.session.delete(course)
    db.session.commit()
    return redirect(url_for('list_courses'))



@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip()
        password = (request.form.get('password') or '').strip()
        role = (request.form.get('role') or '').strip()

        #backend validation
        
        if not username:
            flash('username is required','error')
            return render_template('register.html',error='Username is required',username=username)
        if not email:
            flash('Email is required','error')
            return render_template('register.html',error='Email is required',email=email)
        
        if '@' not in email:
            flash('Provide a valid email','error') 
            return render_template('register.html',error='provide a proper email',username=username)
        
        if not password:
            flash('Password is required','error')
            return render_template('register.html',error='password is required',username=username,email=email,role=role)
        
        if len(password)<4:
            flash('Password must be atleast 4 characters','error')
            return render_template('register.html',error='Password must be atleast 4 characters',username=username,email=email,role=role)

        if role not in ('student','teacher'):
            flash('Please select a valid role','error')
            return render_template('register.html',error='Please selecct a valid role',username=username,email=email,role=role)

        if User.query.filter_by(username=username).first():
            flash('Username already exist','error') 
            return render_template('register.html',error='Username is already taken',username=username,email=email,role=role)
        
        if User.query.filter_by(email=email).first():
            flash('email already exist','error') 
            return render_template('register.html',error='email is already taken',username=username,email=email,role=role)
        
        
        
        try:
            hashed_password = generate_password_hash(password)
            user = User(username=username, email=email, password=hashed_password, role=role)
            db.session.add(user)
            db.session.commit()
            flash('registration successful','success')
            return redirect(url_for('list_users'))
        except Exception as e:
            print("ERROR:", e) 
            db.session.rollback()
            flash('Something went wrong,Please try again','error')
            return render_template('register.html',username=username,email=email,role=role)

        # # If the role is teacher, create teacher record
        # if role == "teacher":
        #     teacher = Teacher(
        #     user_id=user.id,                                          this code is used before the try and except code now it is updated
        #     name=username
        #     )
        #     db.session.add(teacher)
        #     db.session.commit()

        # return redirect(url_for('list_users'))
        # # return redirect(url_for('user_detail.html'))
    return render_template('register.html')


@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'),403

if __name__=='__main__':
    with app.app_context():
        db.create_all()
        print('database tables created')
    app.run(debug=True)


