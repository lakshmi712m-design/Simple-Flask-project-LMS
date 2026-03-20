from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(100),unique=True)
    email=db.Column(db.String(100),unique=True)
    password=db.Column(db.String(20))
    roles=db.Column(db.String(20))

class Student(db.Model):
    
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    name=db.Column(db.String(20))
    enrollments=db.relationship('Enrollement',backref='student')

class Teacher(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name=db.Column(db.String(100))
    courses = db.relationship('Course', backref='teacher')


class Course(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    teacher_id=db.Column(db.Integer,db.ForeignKey('teacher.id'))
    title=db.Column(db.String(80))
    description=db.Column(db.String(100))
    enrollments=db.relationship('Enrollement',backref='course')

class Enrollement(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    student_id=db.Column(db.Integer,db.ForeignKey('student.id'))
    course_id=db.Column(db.Integer,db.ForeignKey('course.id'))
