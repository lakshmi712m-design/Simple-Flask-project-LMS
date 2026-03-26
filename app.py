from flask import Flask,render_template,request,redirect,url_for,flash,session,abort,jsonify
import mysql.connector
from functools import wraps
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.utils import secure_filename
import os
from werkzeug.security import generate_password_hash, check_password_hash
from models import db,User,Course,Enrollment,Video

app=Flask(__name__)

# conn= mysql.connector.connect(
#     host="localhost",
#     user="lms_user",
#     password="lms_password",
#     database="lms_db"
# )

# cursor=conn.cursor()
print("connected to lms database")




app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql+mysqlconnector://lms_user:lms_password@localhost/lms_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SECRET_KEY'] = 'LMS'

app.config['SESSION_COOKIE_HTTPONLY']= True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

app.config['UPLOAD_FOLDER']='FLASK_PROJECT/static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

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


@app.route('/api/users')
@api_login_required
def api_list_users():

    """REST: GET - list users as JSON."""


    users = User.query.all()


    data = [

        {'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role}

        for u in users

    ]


    return jsonify({'status': 'success', 'data': data}), 200



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





@app.route('/api/courses', methods=['POST'])
@api_login_required
@api_role_required('teacher')
def api_create_course():

    """REST: POST - create course (teacher only)."""


    data = _get_api_data()


    title = (data.get('title') or '').strip()

    description = (data.get('description') or '').strip()

    teacher_id = data.get('teacher_id') or session.get('user_id')


    if not title:

        return jsonify({'status': 'error', 'message': 'Title is required'}), 400


    teacher = User.query.filter_by(id=teacher_id, role='teacher').first()


    if not teacher:

        return jsonify({'status': 'error', 'message': 'Invalid teacher'}), 400


    try:

        course = Course(

            title=title,

            description=description,

            teacher_id=teacher_id

        )


        db.session.add(course)

        db.session.commit()


        return jsonify({

            'status': 'success',

            'message': 'Course created',

            'data': {'id': course.id}

        }), 201


    except Exception:

        db.session.rollback()


        return jsonify({

            'status': 'error',

            'message': 'Something went wrong'

        }), 500




@app.route('/api/courses/<int:id>', methods=['PUT'])
@api_login_required
@api_role_required('teacher')
def api_update_course(id):

    """REST: PUT - update course (teacher, own course only)."""


    course = Course.query.get(id)


    if not course:

        return jsonify({'status': 'error', 'message': 'Course not found'}), 404


    if course.teacher_id != session.get('user_id'):

        return jsonify({'status': 'error', 'message': 'Access denied'}), 403


    data = _get_api_data()


    title = (data.get('title') or course.title).strip()

    description = (data.get('description') or course.description or '').strip()


    if not title:

        return jsonify({'status': 'error', 'message': 'Title is required'}), 400


    try:

        course.title = title

        course.description = description


        db.session.commit()


        return jsonify({

            'status': 'success',

            'message': 'Course updated'

        }), 200


    except Exception:

        db.session.rollback()


        return jsonify({

            'status': 'error',

            'message': 'Something went wrong'

        }), 500



@app.route('/api/courses/<int:id>', methods=['DELETE'])
@api_login_required
@api_role_required('teacher')
def api_delete_course(id):

    """REST: DELETE - delete course (teacher, own course only)."""


    course = Course.query.get(id)


    if not course:

        return jsonify({'status': 'error', 'message': 'Course not found'}), 404


    if course.teacher_id != session.get('user_id'):

        return jsonify({'status': 'error', 'message': 'Access denied'}), 403


    try:

        Enrollment.query.filter_by(course_id=id).delete()

        db.session.delete(course)

        db.session.commit()


        return jsonify({

            'status': 'success',

            'message': 'Course deleted'

        }), 200


    except Exception:

        db.session.rollback()


        return jsonify({

            'status': 'error',

            'message': 'Something went wrong'

        }), 500



@app.route('/api/enrollments', methods=['POST'])

@api_login_required

@api_role_required('student')

def api_enroll():

    """REST: POST - enroll in course (student)."""


    data = _get_api_data()

    course_id = data.get('course_id')


    if not course_id:

        return jsonify({'status': 'error', 'message': 'course_id is required'}), 400


    course = Course.query.get(course_id)


    if not course:

        return jsonify({'status': 'error', 'message': 'Course not found'}), 404


    user_id = session.get('user_id')


    existing = Enrollment.query.filter_by(

        user_id=user_id,

        course_id=course_id

    ).first()


    if existing:

        return jsonify({

            'status': 'error',

            'message': 'Already enrolled or pending'

        }), 400


    try:

        enrollment = Enrollment(

            user_id=user_id,

            course_id=course_id,

            status='pending'

        )


        db.session.add(enrollment)

        db.session.commit()


        return jsonify({

            'status': 'success',

            'message': 'Enrollment requested',

            'data': {'id': enrollment.id}

        }), 201


    except Exception:

        db.session.rollback()


        return jsonify({

            'status': 'error',

            'message': 'Something went wrong'

        }), 500



@app.route('/api/enrollments')

@api_login_required

def api_list_enrollments():

    """REST: GET - student: my enrollments; teacher: pass course_id for course enrollments."""



    user_id = session.get('user_id')

    role = session.get('role')

    course_id = request.args.get('course_id', type=int)


    if role == 'student':

        enrollments = Enrollment.query.filter_by(user_id=user_id)\
            .order_by(Enrollment.created_at.desc())\
                .all()


    elif role == 'teacher' and course_id:

        course = Course.query.get(course_id)


        if not course or course.teacher_id != user_id:

            return jsonify({'status': 'error', 'message': 'Access denied'}), 403


        enrollments = Enrollment.query.filter_by(course_id=course_id)\
            .order_by(Enrollment.created_at.desc())\
                .all()


    else:

        return jsonify({

            'status': 'error',

            'message': 'Students: no params. Teachers: course_id required'

        }), 400


    data = [

        {

            'id': e.id,

            'course_id': e.course_id,

            'course_title': e.course.title,

            'user_id': e.user_id,

            'username': e.user.username,

            'status': e.status

        }

        for e in enrollments

    ]


    return jsonify({'status': 'success', 'data': data}), 200



@app.route('/courses')
@login_required
def list_courses():
    courses= Course.query.all()
    return render_template('course_list.html', courses=courses)


# api course list code

@app.route('/api/courses')
@api_login_required
def api_list_courses():

    """REST: GET - list courses as JSON."""


    courses = Course.query.all()


    data = [

        {
            'id': c.id,

            'title': c.title,

            'description': c.description or '',

            'teacher_id': c.teacher_id,

            'status': c.status

        }

        for c in courses
    ]

    return jsonify({

        'status': 'success',

        'data': data

    }), 200

# api course detail

@app.route('/api/courses/<int:id>')

@api_login_required

def api_course_detail(id):

    """REST: GET - course detail. 404 if not found."""


    course = Course.query.get(id)


    if not course:

        return jsonify({

            'status': 'error',

            'message': 'Course not found'

        }), 404


    data = {

        'id': course.id,

        'title': course.title,

        'description': course.description or '',

        'teacher_id': course.teacher_id,

        'teacher': course.teacher.username

    }


    return jsonify({

        'status': 'success',

        'data': data

    }), 200


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


@app.route('/api/users', methods=['POST'])

def api_register():

    """REST: POST - register user. 201 Created, 400 validation error."""

    data = _get_api_data()

    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    role = (data.get('role') or '').strip()

    if isinstance(username, list):
        username = (username[0] or '').strip() if username else ''

    if isinstance(email, list):
        email = (email[0] or '').strip() if email else ''


    if isinstance(password, list):
        password = (password[0] or '').strip() if password else ''
    
    if isinstance(role, list):
        role = (role[0] or '').strip() if role else ''

    if not username:
        return jsonify({"status": "error","message": "Username is required"}),400
    
    if not email or '@' not in email:
        return jsonify({"status": "error","message": "valid email is required"}),400
    
    if not password or len(password)<4:
        return jsonify({"status": "error","message": "minimum 4 characters is required in password"}),400
    
    if not role in ('student','teacher'):
        return jsonify({"status": "error","message": "role must be student or teacher"}),400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"status": "error","message": "Username already exist"}),400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"status": "error","message": "email already exist"}),400
    try:
        user = User(

        username=username,

        email=email,

        password=generate_password_hash(password),

        role=role)
        db.session.add(user)
        db.session.commit()
        return jsonify({"status": "success","message": "registration successfull"

        }),201
    except Exception:
        db.session.rollback()
        return jsonify({"status": "error","message": "Something went wrong"}),500


def _get_api_data():

    """Get request data from JSON, form, or query string (for API flexibility)."""


    # 1. Try JSON body

    data = request.get_json(force=True, silent=True)

    if data and isinstance(data, dict):

        return data


    # 2. Try form data

    if request.form:

        return {

            k: (v[0] if isinstance(v, list) else v)

            for k, v in request.form.items()

        }


    # 3. Try raw body JSON

    if request.get_data():

        import json

        try:

            return json.loads(request.get_data(as_text=True))

        except Exception:

            pass


    # 4. Try query parameters

    if request.args:

        return dict(request.args)


    return {}




@app.route('/api/login', methods=['POST'])

def api_login():

    """REST: POST - login. Returns 200 + session, 401 if invalid."""


    data = _get_api_data()


    username = (data.get('username') or '').strip()

    password = data.get('password') or ''


    if not username or not password:

        return jsonify({'status': 'error', 'message': 'Username and password required'}), 400


    user = User.query.filter_by(username=username).first()


    if not user or not check_password_hash(user.password, password):

        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401


    session['user_id'] = user.id

    session['role'] = user.role

    session['username'] = user.username

    session.permanent = True


    return jsonify({

        'status': 'success',

        'message': 'Login successful',

        'data': {'user_id': user.id, 'role': user.role}

    }), 200


@app.route('/course/<int:id>/video/create', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def create_video(id):
    course = Course.query.get_or_404(id)

    if course.teacher_id != session.get('user_id'):
        abort(403)

    if request.method== 'POST':
        title = (request.form.get('title') or '').strip()
        file = request.files.get('file')

        if not title:
            flash('Title is required.', 'error')
            return render_template('video_form.html',course=course)
        
        if not file or file.filename == '':
            flash('File is required','error')
            return render_template('video_form.html',course=course)
        
        filename = secure_filename(file.filename)

        if not filename:
            flash('Invalid file name','error')
            return render_template('video_form.html',course=course,title=title)
        
        upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'videos')

        os.makedirs(upload_dir, exist_ok=True)

        ext = os.path.splitext(filename)[1] or '.mp4'

        unique_name = f"{course.id}_{Video.query.filter_by(course_id=id).count() + 1}{ext}"

        file_path = os.path.join(upload_dir, unique_name)
        file.save(file_path)

        rel_path = f"uploads/videos/{unique_name}"

        video = Video(
            course_id=id,
            title=title,
            file_path=rel_path)
        
        db.session.add(video)
        db.session.commit()

        flash('video added','success')

        return redirect(url_for('list_videos', id=id))
    
    return render_template('video_form.html',course=course)
        

@app.route('/course/<int:id>/videos')

@login_required

def list_videos(id):

    """List videos for a course."""

    course = Course.query.get_or_404(id)

    videos = Video.query.filter_by(course_id=id).order_by(Video.order, Video.id).all()

    return render_template('video_list.html', course=course, videos=videos)



@app.route('/video/delete/<int:id>')
@login_required
@role_required('teacher')
def delete_video(id):

    """Delete video (teacher, own course only)."""

    video = Video.query.get_or_404(id)

    course = Course.query.get_or_404(video.course_id)


    if course.teacher_id != session.get('user_id'):

        abort(403)


    db.session.delete(video)

    db.session.commit()


    flash('Video deleted.', 'success')

    return redirect(url_for('list_videos', id=course.id))



@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'),403

if __name__=='__main__':
    with app.app_context():
        db.create_all()
        print('database tables created')
    app.run(debug=True)


