from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json as json_module
from markupsafe import escape
from models import db, Event, Resource, EventResourceAllocation
from forms import EventForm, ResourceForm, AllocationForm, ReportForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Nallni%4005@localhost/event_scheduler_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.template_filter('escapejs')
def escapejs_filter(value):
    """Escape string for JavaScript."""
    if value is None:
        return ''
    value = str(value)
    value = value.replace('\\', '\\\\')
    value = value.replace("'", "\\'")
    value = value.replace('"', '\\"')
    value = value.replace('\n', '\\n')
    value = value.replace('\r', '\\r')
    value = value.replace('\t', '\\t')
    return escape(value)

@app.template_filter('tojson')
def tojson_filter(value):
    """Convert to JSON string."""
    return json_module.dumps(value)

@app.context_processor
def inject_datetime():
    return dict(datetime=datetime, now=datetime.now())

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    events = Event.query.all()
    resources = Resource.query.all()
    allocations = EventResourceAllocation.query.all()

    conflicts_list = []
    allocations_all = EventResourceAllocation.query.all()
    resource_schedule = {}
    
    for alloc in allocations_all:
        event = Event.query.get(alloc.event_id)
        resource = Resource.query.get(alloc.resource_id)
        
        if alloc.resource_id not in resource_schedule:
            resource_schedule[alloc.resource_id] = []
        
        for scheduled_event in resource_schedule[alloc.resource_id]:
            if (event.start_time < scheduled_event['end_time'] and 
                event.end_time > scheduled_event['start_time']):
                conflicts_list.append({
                    'resource': resource.resource_name,
                    'conflict_event1': scheduled_event['title'],
                    'conflict_event2': event.title
                })
        
        resource_schedule[alloc.resource_id].append({
            'title': event.title,
            'start_time': event.start_time,
            'end_time': event.end_time
        })
    
    return render_template('index.html', 
                         events=events,
                         resources=resources,
                         allocations=allocations,
                         conflicts=conflicts_list)

@app.route('/events')
def events():
    events_list = Event.query.all()
    return render_template('events.html', events=events_list)

@app.route('/events/add', methods=['GET', 'POST'])
def add_event():
    form = EventForm()
    if form.validate_on_submit():
        start_datetime = datetime.combine(form.event_date.data, form.start_time.data)
        end_datetime = datetime.combine(form.event_date.data, form.end_time.data)
 
        if form.end_time.data <= form.start_time.data:
            end_datetime += timedelta(days=1)

        conflicting_events = Event.query.filter(
            Event.start_time < end_datetime,
            Event.end_time > start_datetime,
            Event.event_id != form.event_id.data if form.event_id.data else None
        ).all()
        
        if conflicting_events:
            flash('Time conflict detected with existing events!', 'danger')
            return render_template('event_form.html', form=form, title='Add Event')
        
        event = Event(
            title=form.title.data,
            start_time=start_datetime,
            end_time=end_datetime,
            description=form.description.data
        )
        db.session.add(event)
        db.session.commit()
        flash('Event added successfully!', 'success')
        return redirect(url_for('events'))

    if not form.event_date.data:
        form.event_date.data = datetime.now().date()
    
    return render_template('event_form.html', form=form, title='Add Event')

@app.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)

    form = EventForm(obj=event)

    if event.start_time:
        form.event_date.data = event.start_time.date()
        form.start_time.data = event.start_time.time()
        form.end_time.data = event.end_time.time()
    
    if form.validate_on_submit():
        start_datetime = datetime.combine(form.event_date.data, form.start_time.data)
        end_datetime = datetime.combine(form.event_date.data, form.end_time.data)
 
        if form.end_time.data <= form.start_time.data:
            end_datetime += timedelta(days=1)
  
        conflicting_events = Event.query.filter(
            Event.start_time < end_datetime,
            Event.end_time > start_datetime,
            Event.event_id != event_id
        ).all()
        
        if conflicting_events:
            flash('Time conflict detected with existing events!', 'danger')
            return render_template('event_form.html', form=form, title='Edit Event')

        event.title = form.title.data
        event.start_time = start_datetime
        event.end_time = end_datetime
        event.description = form.description.data
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('events'))
    
    return render_template('event_form.html', form=form, title='Edit Event')

@app.route('/events/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    EventResourceAllocation.query.filter_by(event_id=event_id).delete()
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('events'))

@app.route('/resources')
def resources():
    resources_list = Resource.query.all()
    return render_template('resources.html', resources=resources_list)

@app.route('/resources/add', methods=['GET', 'POST'])
def add_resource():
    form = ResourceForm()
    if form.validate_on_submit():
        resource = Resource(
            resource_name=form.resource_name.data,
            resource_type=form.resource_type.data
        )
        db.session.add(resource)
        db.session.commit()
        flash('Resource added successfully!', 'success')
        return redirect(url_for('resources'))
    
    return render_template('resource_form.html', form=form, title='Add Resource')

@app.route('/resources/edit/<int:resource_id>', methods=['GET', 'POST'])
def edit_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    form = ResourceForm(obj=resource)
    
    if form.validate_on_submit():
        form.populate_obj(resource)
        db.session.commit()
        flash('Resource updated successfully!', 'success')
        return redirect(url_for('resources'))
    
    return render_template('resource_form.html', form=form, title='Edit Resource')

@app.route('/resources/delete/<int:resource_id>', methods=['POST'])
def delete_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    EventResourceAllocation.query.filter_by(resource_id=resource_id).delete()
    db.session.delete(resource)
    db.session.commit()
    flash('Resource deleted successfully!', 'success')
    return redirect(url_for('resources'))

@app.route('/allocations')
def allocations():
    allocations_list = EventResourceAllocation.query.all()
    events = Event.query.all()
    resources = Resource.query.all()

    events_dict = {e.event_id: e for e in events}
    resources_dict = {r.resource_id: r for r in resources}
    
    return render_template('allocations.html', 
                         allocations=allocations_list,
                         events=events,
                         resources=resources,
                         events_dict=events_dict,
                         resources_dict=resources_dict)

@app.route('/allocations/add', methods=['GET', 'POST'])
def add_allocation():
    form = AllocationForm()
    all_events = Event.query.all()
    all_resources = Resource.query.all()
    
    form.event_id.choices = [(e.event_id, e.title) for e in all_events]
    form.resource_id.choices = [(r.resource_id, f"{r.resource_name} ({r.resource_type})") 
                               for r in all_resources]
  
    events_data = []
    for event in all_events:
        events_data.append({
            'event_id': event.event_id,
            'title': event.title,
            'start_time': event.start_time.isoformat() if event.start_time else None,
            'end_time': event.end_time.isoformat() if event.end_time else None,
            'description': event.description
        })
    
    resources_data = []
    for resource in all_resources:
        resources_data.append({
            'resource_id': resource.resource_id,
            'resource_name': resource.resource_name,
            'resource_type': resource.resource_type
        })
    
    if form.validate_on_submit():
        event = Event.query.get(form.event_id.data)
        
        conflicting_allocations = db.session.query(EventResourceAllocation).join(Event).filter(
            EventResourceAllocation.resource_id == form.resource_id.data,
            Event.start_time < event.end_time,
            Event.end_time > event.start_time
        ).all()
        
        if conflicting_allocations:
            flash(f'Resource already allocated during this time period!', 'danger')
            return render_template('allocation_form.html', 
                                   form=form, 
                                   title='Allocate Resource',
                                   events=events_data,
                                   resources=resources_data)
        
        allocation = EventResourceAllocation(
            event_id=form.event_id.data,
            resource_id=form.resource_id.data
        )
        db.session.add(allocation)
        db.session.commit()
        flash('Resource allocated successfully!', 'success')
        return redirect(url_for('allocations'))
    
    return render_template('allocation_form.html', 
                         form=form, 
                         title='Allocate Resource',
                         events=events_data,
                         resources=resources_data)

@app.route('/allocations/delete/<int:allocation_id>', methods=['POST'])
def delete_allocation(allocation_id):
    allocation = EventResourceAllocation.query.get_or_404(allocation_id)
    db.session.delete(allocation)
    db.session.commit()
    flash('Allocation deleted successfully!', 'success')
    return redirect(url_for('allocations'))

@app.route('/conflicts')
def conflicts():
    conflicts_list = []
    all_resources = Resource.query.all()

    allocations = EventResourceAllocation.query.all()

    resource_schedule = {}
    
    for alloc in allocations:
        event = Event.query.get(alloc.event_id)
        resource = Resource.query.get(alloc.resource_id)
        
        if alloc.resource_id not in resource_schedule:
            resource_schedule[alloc.resource_id] = []
        
        for scheduled_event in resource_schedule[alloc.resource_id]:
            if (event.start_time < scheduled_event['end_time'] and 
                event.end_time > scheduled_event['start_time']):
                conflicts_list.append({
                    'resource': resource.resource_name,
                    'resource_type': resource.resource_type,
                    'conflict_event1': scheduled_event['title'],
                    'conflict_event2': event.title,
                    'overlap_period': f"{max(event.start_time, scheduled_event['start_time'])} to {min(event.end_time, scheduled_event['end_time'])}"
                })
        
        resource_schedule[alloc.resource_id].append({
            'title': event.title,
            'start_time': event.start_time,
            'end_time': event.end_time
        })
    
    return render_template('conflicts.html', conflicts=conflicts_list, all_resources=all_resources)

@app.route('/report', methods=['GET', 'POST'])
def report():
    form = ReportForm()
    report_data = []
    
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data

        end_date = datetime.combine(end_date, datetime.max.time())

        resources = Resource.query.all()
        
        for resource in resources:
            allocations = db.session.query(EventResourceAllocation).join(Event).filter(
                EventResourceAllocation.resource_id == resource.resource_id,
                Event.start_time >= start_date,
                Event.start_time <= end_date
            ).all()
            
            total_hours = 0
            upcoming_bookings = []
            
            for alloc in allocations:
                event = Event.query.get(alloc.event_id)
                duration = (event.end_time - event.start_time).total_seconds() / 3600
                total_hours += duration
                
                if event.start_time > datetime.now():
                    upcoming_bookings.append({
                        'event': event.title,
                        'start_time': event.start_time,
                        'end_time': event.end_time
                    })
            
            report_data.append({
                'resource_name': resource.resource_name,
                'resource_type': resource.resource_type,
                'total_hours': round(total_hours, 2),
                'upcoming_bookings': upcoming_bookings,
                'booking_count': len(upcoming_bookings)
            })
    
    return render_template('report.html', form=form, report_data=report_data)

@app.route('/api/check_conflict', methods=['POST'])
def check_conflict():
    data = request.json
    event_id = data.get('event_id')
    resource_ids = data.get('resource_ids', [])
    start_time = datetime.fromisoformat(data['start_time'])
    end_time = datetime.fromisoformat(data['end_time'])
    
    conflicts = []
    
    for resource_id in resource_ids:
        overlapping = db.session.query(Event).join(EventResourceAllocation).filter(
            EventResourceAllocation.resource_id == resource_id,
            Event.start_time < end_time,
            Event.end_time > start_time,
            Event.event_id != event_id if event_id else True
        ).all()
        
        if overlapping:
            resource = Resource.query.get(resource_id)
            for event in overlapping:
                conflicts.append({
                    'resource': resource.resource_name,
                    'conflicting_event': event.title,
                    'period': f"{event.start_time} to {event.end_time}"
                })
    
    return jsonify({'has_conflicts': len(conflicts) > 0, 'conflicts': conflicts})

if __name__ == '__main__':
    app.run(debug=True)