from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, SelectField, SubmitField, DateField, TimeField
from wtforms.validators import DataRequired, ValidationError
from datetime import datetime, time

class EventForm(FlaskForm):
    event_id = StringField('Event ID')  
    title = StringField('Title', validators=[DataRequired()])
    event_date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    start_time = TimeField('Start Time', format='%H:%M', validators=[DataRequired()])
    end_time = TimeField('End Time', format='%H:%M', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Save')
    
    def validate_end_time(self, field):
        if self.start_time.data and field.data:
            if field.data <= self.start_time.data:
                raise ValidationError('End time must be after start time')

class ResourceForm(FlaskForm):
    resource_name = StringField('Resource Name', validators=[DataRequired()])
    resource_type = SelectField('Resource Type', 
                              choices=[('room', 'Room'), 
                                      ('instructor', 'Instructor'), 
                                      ('equipment', 'Equipment'),
                                      ('other', 'Other')],
                              validators=[DataRequired()])
    submit = SubmitField('Save')

class AllocationForm(FlaskForm):
    event_id = SelectField('Event', coerce=int, validators=[DataRequired()])
    resource_id = SelectField('Resource', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Allocate')

class ReportForm(FlaskForm):
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Generate Report')
    
    def validate_end_date(self, field):
        if self.start_date.data and field.data:
            if field.data < self.start_date.data:
                raise ValidationError('End date must be after start date')