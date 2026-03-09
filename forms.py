from flask_wtf import FlaskForm
from wtforms import EmailField, IntegerField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, Regexp, ValidationError


class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=80)])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField(
        'Phone',
        validators=[
            DataRequired(),
            Regexp(r'^\+?[0-9]{10,15}$', message='Phone number must be 10 to 15 digits (optional + prefix).'),
        ],
    )
    district = StringField('District', validators=[DataRequired(), Length(min=2, max=80)])
    panchayat = StringField('Panchayat', validators=[DataRequired(), Length(min=2, max=80)])
    ward_number = IntegerField('Ward Number', validators=[DataRequired(), NumberRange(min=1, max=1000)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords do not match')],
    )


class ComplaintSubmissionForm(FlaskForm):
    title = StringField('Complaint Title', validators=[DataRequired(), Length(min=5, max=150)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=2000)])
    category = SelectField(
        'Category',
        validators=[DataRequired()],
        choices=[
            ('Electrical', 'Electricity & Streetlights'),
            ('Sanitation', 'Garbage & Sanitation'),
            ('Roads', 'Roads & Infrastructure'),
            ('Water', 'Water Supply'),
            ('Other', 'Other'),
        ],
    )
    latitude = StringField('Latitude', validators=[Optional()])
    longitude = StringField('Longitude', validators=[Optional()])

    def validate_latitude(self, field):
        if not field.data:
            return
        try:
            value = float(field.data)
        except (TypeError, ValueError) as exc:
            raise ValidationError('Latitude must be a valid number.') from exc
        if value < -90 or value > 90:
            raise ValidationError('Latitude must be between -90 and 90.')
        field.data = value

    def validate_longitude(self, field):
        if not field.data:
            return
        try:
            value = float(field.data)
        except (TypeError, ValueError) as exc:
            raise ValidationError('Longitude must be a valid number.') from exc
        if value < -180 or value > 180:
            raise ValidationError('Longitude must be between -180 and 180.')
        field.data = value
