from flask import Flask,render_template,request,redirect,url_for,flash
import mysql.connector
from flask_sqlalchemy import SQLAlchemy 
from models import db,User,Course,Teacher

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

db.init_app(app)


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/users')
def list_users():
    users= User.query.all()
    return render_template('user_list.html',users=users)


@app.route('/user/edit/<int:id>', methods=['GET', 'POST'])

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
        
        if User.query.filter_by(username=username).first():
            flash('Username already exist','error') 
            return render_template('user_edit.html',user=user)
        
        if User.query.filter_by(email=email).first():
            flash('email already exist','error') 
            return render_template('user_edit.html',user=user)
        
        try:

            user.username=username
            user.email=email
            user.password=password
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
def user_detail(id):
    user=User.query.get_or_404(id)
    return render_template('user_detail.html',user=user)

@app.route('/user/delete/<int:id>')
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
#     teachers=User.query.filter_by(roles='teacher').all()
#     return render_template('course_form.html',teachers=teachers)



@app.route('/course/create', methods=['GET', 'POST'])
def course_create():

    if request.method == 'POST':

        title = (request.form.get('title') or '').strip()
        description = (request.form.get('description')or '').strip()
        teacher_id_raw = request.form.get('teacher_id', '').strip()

        #backend validation

        if not title:
            flash('Course title is required','error')
            teachers=User.query.filter_by(role=teachers).all()
            return render_template('course_form.html',teachers=teachers,title=title,description=description)
        
        if not teacher_id_raw:
            flash('Please select a teacher')
            teachers=User.query.filter_by(role=teachers).all()
            return render_template('course_form.html',teachers=teachers,title=title,description=description)
        

        try:
            teacher_id=int(teacher_id_raw)
        except ValueError:
            flash('Invalid teacher id','error')
            teachers=User.query.filter_by(role=teachers).all()
            return render_template('course_form.html',teachers=teachers,title=title,description=description)
        
        teacher = Teacher.query.filter_by(id=teacher_id).first()
        if not teacher:
            flash('Invalid teacher selected','error')
            teachers=User.query.filter_by(roles='teacher').all()
            return render_template('course_form.html',teachers=teachers,title=title,description=description)
        
        try:
            course = Course(
                title=title,
                description=description,
                teacher_id=teacher_id
            )

            db.session.add(course)
            db.session.commit()
            flash('Course created successfully','success')

            return redirect(url_for('list_courses'))
        except Exception:
            db.session.rollback()
            flash('Something went wrong,Please try again later','error')
            teachers=User.query.filter_by(roles='teacher').all()
            return render_template('course_form.html',teachers=teachers,title=title,description=description)
        

    teachers = Teacher.query.all()

    return render_template('course_form.html', teachers=teachers)


@app.route('/courses')
def list_courses():
    courses= Course.query.all()
    return render_template('course_list.html', courses=courses)


@app.route('/course/<int:id>')
def course_detail(id):
    course=Course.query.get_or_404(id)
    return render_template('course_detail.html',course=course)

@app.route('/course/edit/<int:id>',methods=['GET', 'POST'])
def course_edit(id):
    course = Course.query.get_or_404(id)
    teachers = Teacher.query.all()

    if request.method == 'POST':
        title = (request.form.get('title')or '').strip()
        description = (request.form.get('description') or '').strip()
        teacher_id_raw = (request.form.get('teacher_id') or '').strip()
    
    
        #backend validation

        if not title:
            flash('Course title is required','error')
            teachers=User.query.filter_by(role=teachers).all()
            return render_template('course_edit.html',teachers=teachers,course=course)
        
        if not teacher_id_raw:
            flash('Please select a teacher')
            teachers=User.query.filter_by(role=teachers).all()
            return render_template('course_edit.html',teachers=teachers,course=course)
        
        try:
            teacher_id=int(teacher_id_raw)
        except ValueError:
            flash('Invalid teacher id','error')
            teachers=User.query.filter_by(role=teachers).all()
            return render_template('course_edit.html',teachers=teachers,course=course)
        
        
        teacher = Teacher.query.filter_by(id=teacher_id).first()
        if not teacher:
            flash('Invalid teacher selected','error')
            teachers=User.query.filter_by(roles='teacher').all()
            return render_template('course_edit.html',teachers=teachers,course=course)
        

        try:

            course.title=title
            course.description=description
            course.teacher_id=teacher_id    

            db.session.commit()
            flash('Course updated successfully','success')
            return redirect(url_for('list_courses'))
        except Exception:
            db.session.rollback()
            flash('Something went wrong,Please try again','error')
            return render_template('course_edit.html',teachers=teachers,course=course)

    return render_template('course_edit.html', course=course, teachers=teachers)

@app.route('/course/delete/<int:id>')

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
            user = User(username=username, email=email, password=password, roles=role)
            db.session.add(user)
            db.session.commit()
            flash('registration successful','success')
            return redirect(url_for('list_users'))
        except Exception:
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


if __name__=='__main__':
    with app.app_context():
        db.create_all()
        print('database tables created')
    app.run(debug=True)


