from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
# db instance will be set by app.py
db = SQLAlchemy()


class User(db.Model):
    """User table: students and teachers. Role stored here"""
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) 
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"


class Course(db.Model):
    """Course table: one course belongs to one teacher"""
    __tablename__ = "course"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # relationship: courses belong to a teacher
    teacher = db.relationship('User', backref='courses')

    def __repr__(self):
        return f"<Course {self.name}>"
    

class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')
    def __repr__(self):
        return f"<Enrollment user={self.user_id} course={self.course_id} {self.status}>"