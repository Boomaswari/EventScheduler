from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = 'event'
    
    event_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    
    resources = db.relationship('Resource', secondary='event_resource_allocation')
    allocations = db.relationship('EventResourceAllocation', backref='event', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Event {self.title}>'

class Resource(db.Model):
    __tablename__ = 'resource'
    
    resource_id = db.Column(db.Integer, primary_key=True)
    resource_name = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  
    
    events = db.relationship('Event', secondary='event_resource_allocation')
    allocations = db.relationship('EventResourceAllocation', backref='resource', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Resource {self.resource_name}>'

class EventResourceAllocation(db.Model):
    __tablename__ = 'event_resource_allocation'
    
    allocation_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id', ondelete='CASCADE'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.resource_id', ondelete='CASCADE'), nullable=False)
 
    __table_args__ = (db.UniqueConstraint('event_id', 'resource_id', name='unique_event_resource'),)
    
    def __repr__(self):
        return f'<Allocation Event:{self.event_id} Resource:{self.resource_id}>'