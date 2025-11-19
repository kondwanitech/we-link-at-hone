from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, ValidationError, EqualTo
import re


def validate_password_strength(form, field):
    """
    Validate password meets security requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one special character
    """
    password = field.data
    
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must include at least one uppercase letter.')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;~`]', password):
        raise ValidationError('Password must include at least one special character.')


def validate_student_number(form, field):
    """
    Validate student number is between 10-12 characters.
    """
    student_number = field.data
    
    if len(student_number) < 10 or len(student_number) > 12:
        raise ValidationError('Student number must be between 10 and 12 characters.')


class RegisterForm(FlaskForm):
    student_number = StringField('Student Number', validators=[
        DataRequired(message='Student number is required.'),
        validate_student_number
    ])
    name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required.'),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Invalid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        validate_password_strength
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])


class AdminCreateStudentForm(FlaskForm):
    student_number = StringField('Student Number', validators=[
        DataRequired(message='Student number is required.'),
        validate_student_number
    ])
    name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required.'),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Invalid email address.')
    ])
    temp_password = PasswordField('Temporary Password', validators=[
        DataRequired(message='Temporary password is required.'),
        validate_password_strength
    ])


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required.')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required.'),
        validate_password_strength
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password.'),
        EqualTo('new_password', message='Passwords must match.')
    ])
