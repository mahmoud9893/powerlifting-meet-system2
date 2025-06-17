# MBR - ULTIMATE FIX ATTEMPT: NO @app.before_first_request, Flask-SQLAlchemy, and VERSION CHECK - June 17, 2025
import os
import json
from datetime import datetime, date
from flask import Flask, request, jsonify # Import Flask here
import flask # Import the flask module itself to get version
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import pandas as pd
from io import BytesIO
from sqlalchemy import inspect # Import inspect for checking table existence

print(f"Application starting. Running with Flask version: {flask.__version__}")

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Configure SQLAlchemy for PostgreSQL using an environment variable
# If DATABASE_URL is not set (e.g., during local development), it falls back to SQLite.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'powerlifting_meet.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
# Explicitly allow your Netlify frontend domain for Socket.IO
# Keep localhost:8080 for local frontend development
# message_queue=None is important for Cloud Run/Render's stateless nature without a separate Redis/RabbitMQ.
socketio = SocketIO(app, cors_allowed_origins=[
    "https://powerlifting-meet-system26.netlify.app", # Your Netlify domain
    "http://localhost:8080",
    "http://127.0.0.1:8080", # Also common for local
    "*" # Consider making this more restrictive in production
], message_queue=None, async_mode='eventlet') # Ensure eventlet is used for async

# --- Global Meet State ---
current_meet_state = {
    'current_lift_type': 'squat',
    'current_active_lift_id': None,
    'current_attempt_number': 1
}

# --- Hardcoded Judge PINs (for demonstration purposes) ---
JUDGE_PINS = {
    "1234": 1, # Judge 1
    "5678": 2, # Judge 2
    "9012": 3  # Judge 3
}

# --- Database Models ---

class MeetState(db.Model):
    __tablename__ = 'meet_state'
    id = db.Column(db.Integer, primary_key=True, default=1) # Ensure only one row
    current_lift_type = db.Column(db.String(20), default='squat')
    current_active_lift_id = db.Column(db.Integer, db.ForeignKey('lift_attempt.id'), nullable=True)
    current_attempt_number = db.Column(db.Integer, default=1)
    is_meet_active = db.Column(db.Boolean, default=True) # Added for explicit meet start/stop

    # Relationship to LiftAttempt for easier access
    active_lift = db.relationship('LiftAttempt', foreign_keys=[current_active_lift_id], lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'current_lift_type': self.current_lift_type,
            'current_active_lift_id': self.current_active_lift_id,
            'current_attempt_number': self.current_attempt_number,
            'is_meet_active': self.is_meet_active
        }

class AgeClass(db.Model):
    __tablename__ = 'age_class'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    min_age = db.Column(db.Integer, nullable=False)
    max_age = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'min_age': self.min_age,
            'max_age': self.max_age
        }

class WeightClass(db.Model):
    __tablename__ = 'weight_class'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    min_weight = db.Column(db.Float, nullable=False)
    max_weight = db.Column(db.Float, nullable=True)
    gender = db.Column(db.String(10), nullable=False) # 'Male', 'Female', 'Both'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'min_weight': self.min_weight,
            'max_weight': self.max_weight,
            'gender': self.gender
        }

# Association tables for many-to-many additional classes
lifter_additional_weight_class = db.Table('lifter_additional_weight_class',
    db.Column('lifter_id', db.Integer, db.ForeignKey('lifter.id'), primary_key=True),
    db.Column('weight_class_id', db.Integer, db.ForeignKey('weight_class.id'), primary_key=True)
)

lifter_additional_age_class = db.Table('lifter_additional_age_class',
    db.Column('lifter_id', db.Integer, db.ForeignKey('lifter.id'), primary_key=True),
    db.Column('age_class_id', db.Integer, db.ForeignKey('age_class.id'), primary_key=True)
)

class Lifter(db.Model):
    __tablename__ = 'lifter'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    lifter_id_number = db.Column(db.String(50), unique=True, nullable=False)
    actual_weight = db.Column(db.Float, nullable=False)
    birth_date = db.Column(db.Date, nullable=False) # Store as Date object

    # Primary class assignments (automatically determined)
    primary_weight_class_id = db.Column(db.Integer, db.ForeignKey('weight_class.id'), nullable=True)
    primary_weight_class = db.relationship('WeightClass', foreign_keys=[primary_weight_class_id], backref='primary_lifters', lazy=True)

    primary_age_class_id = db.Column(db.Integer, db.ForeignKey('age_class.id'), nullable=True)
    primary_age_class = db.relationship('AgeClass', foreign_keys=[primary_age_class_id], backref='primary_lifters', lazy=True)

    # Many-to-many relationships for additional classes
    additional_weight_classes = db.relationship(
        'WeightClass',
        secondary=lifter_additional_weight_class,
        backref=db.backref('additional_lifters', lazy='dynamic')
    )
    additional_age_classes = db.relationship(
        'AgeClass',
        secondary=lifter_additional_age_class,
        backref=db.backref('additional_lifters', lazy='dynamic')
    )

    lift_attempts = db.relationship('LiftAttempt', backref='lifter', lazy=True, cascade="all, delete-orphan")

    def calculate_age(self):
        today = date.today()
        age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return age

    def assign_primary_classes(self):
        # Assign primary weight class
        self.primary_weight_class = None # Clear existing assignment
        suitable_wc = WeightClass.query.filter(
            WeightClass.min_weight <= self.actual_weight,
            (WeightClass.max_weight >= self.actual_weight) | (WeightClass.max_weight == None),
            (WeightClass.gender == self.gender) | (WeightClass.gender == 'Both')
        ).order_by(WeightClass.max_weight.asc()).first() # Prioritize smaller classes
        if suitable_wc:
            self.primary_weight_class = suitable_wc

        # Assign primary age class
        self.primary_age_class = None # Clear existing assignment
        lifter_age = self.calculate_age()
        if lifter_age is not None:
            suitable_ac = AgeClass.query.filter(
                AgeClass.min_age <= lifter_age,
                (AgeClass.max_age >= lifter_age) | (AgeClass.max_age == None)
            ).order_by(AgeClass.max_age.asc()).first() # Prioritize younger classes
            if suitable_ac:
                self.primary_age_class = suitable_ac

    def to_dict(self):
        additional_wc_names = [wc.name for wc in self.additional_weight_classes]
        additional_ac_names = [ac.name for ac in self.additional_age_classes]
        additional_wc_ids = [wc.id for wc in self.additional_weight_classes]
        additional_ac_ids = [ac.id for ac in self.additional_age_classes]

        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'lifter_id_number': self.lifter_id_number,
            'actual_weight': self.actual_weight,
            'birth_date': self.birth_date.isoformat(), # Format date to string
            'age': self.calculate_age(),
            'primary_weight_class_id': self.primary_weight_class_id,
            'primary_weight_class_name': self.primary_weight_class.name if self.primary_weight_class else 'N/A',
            'primary_age_class_id': self.primary_age_class_id,
            'primary_age_class_name': self.primary_age_class.name if self.primary_age_class else 'N/A',
            'additional_weight_class_names': additional_wc_names,
            'additional_age_class_names': additional_ac_names,
            'additional_weight_class_ids': additional_wc_ids,
            'additional_age_class_ids': additional_ac_ids,
        }

class LiftAttempt(db.Model):
    __tablename__ = 'lift_attempt'
    id = db.Column(db.Integer, primary_key=True)
    lifter_id = db.Column(db.Integer, db.ForeignKey('lifter.id'), nullable=False)
    lift_type = db.Column(db.String(20), nullable=False) # 'squat', 'bench', 'deadlift'
    weight_lifted = db.Column(db.Float, nullable=False)
    attempt_number = db.Column(db.Integer, nullable=False) # 1st, 2nd, 3rd attempt
    status = db.Column(db.String(20), default='pending') # pending, active, completed
    judge1_score = db.Column(db.Boolean, nullable=True) # True for good, False for bad, None for not scored
    judge2_score = db.Column(db.Boolean, nullable=True)
    judge3_score = db.Column(db.Boolean, nullable=True)
    overall_result = db.Column(db.Boolean, nullable=True) # True for good lift, False for no lift
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<LiftAttempt {self.lifter_id} - {self.lift_type} {self.weight_lifted}kg - Attempt {self.attempt_number}>"

    def calculate_overall_result(self):
        scores = [self.judge1_score, self.judge2_score, self.judge3_score]
        actual_scores = [s for s in scores if s is not None]

        if len(actual_scores) < 3: # Need all 3 scores to determine overall result
            self.overall_result = None
            return False # Not enough scores yet

        good_lifts = sum(1 for s in actual_scores if s is True)
        
        if good_lifts >= 2:
            self.overall_result = True
        else:
            self.overall_result = False
        return True # Overall result has been determined

    def to_dict(self):
        lifter = Lifter.query.get(self.lifter_id) # Fetch lifter to get details
        return {
            'id': self.id,
            'lifter_id': self.lifter_id,
            'lifter_name': lifter.name if lifter else 'Unknown',
            'lifter_id_number': lifter.lifter_id_number if lifter else 'Unknown',
            'gender': lifter.gender if lifter else 'Unknown',
            'actual_weight': lifter.actual_weight if lifter else 'Unknown',
            'weight_class_name': lifter.primary_weight_class.name if lifter and lifter.primary_weight_class else 'N/A', # Use primary
            'lift_type': self.lift_type,
            'weight_lifted': self.weight_lifted,
            'attempt_number': self.attempt_number,
            'status': self.status,
            'judge1_score': self.judge1_score,
            'judge2_score': self.judge2_score,
            'judge3_score': self.judge3_score,
            'overall_result': self.overall_result,
            'timestamp': self.timestamp.isoformat() # Include timestamp
        }

# --- Database Initialization & Dummy Data ---
# This block runs within the application context, ensuring Flask-SQLAlchemy is properly initialized.
# It replaces the deprecated @app.before_first_request decorator.
with app.app_context():
    # Check if tables exist before creating.
    inspector = inspect(db.engine)
    
    # Only create tables and seed data if the 'lifter' table (or any other essential table) doesn't exist.
    if not inspector.has_table("lifter") or \
       not inspector.has_table("weight_class") or \
       not inspector.has_table("age_class") or \
       not inspector.has_table("lift_attempt") or \
       not inspector.has_table("meet_state"):
        db.create_all()
        print("Database tables created.")

        # Initialize MeetState (ensure only one row)
        if MeetState.query.count() == 0:
            db.session.add(MeetState(id=1, current_lift_type='squat', current_attempt_number=1, is_meet_active=True))
            db.session.commit()
            print("Initial MeetState created.")

        if WeightClass.query.count() == 0:
            print("Adding dummy weight classes...")
            wc_m83 = WeightClass(name="Men's 83kg", min_weight=74.01, max_weight=83.0, gender="Male")
            wc_m93 = WeightClass(name="Men's 93kg", min_weight=83.01, max_weight=93.0, gender="Male")
            wc_m105 = WeightClass(name="Men's 105kg", min_weight=93.01, max_weight=105.0, gender="Male")
            wc_w69 = WeightClass(name="Women's 69kg", min_weight=63.01, max_weight=69.0, gender="Female")
            wc_w76 = WeightClass(name="Women's 76kg", min_weight=69.01, max_weight=76.0, gender="Female")
            db.session.add_all([wc_m83, wc_m93, wc_m105, wc_w69, wc_w76])
            db.session.commit()
            print("Dummy weight classes added.")

    if AgeClass.query.count() == 0:
        print("Adding dummy age classes...")
        ac_junior = AgeClass(name="Junior (U23)", min_age=18, max_age=23)
        ac_open = AgeClass(name="Open (24-39)", min_age=24, max_age=39)
        ac_masters40 = AgeClass(name="Masters I (40-49)", min_age=40, max_age=49)
        ac_masters50 = AgeClass(name="Masters II (50+)", min_age=50, max_age=None)
        db.session.add_all([ac_junior, ac_open, ac_masters40, ac_masters50])
        db.session.commit()
        print("Dummy age classes added.")

    if Lifter.query.count() == 0:
        print("Adding dummy lifters and attempts...")
        
        lifter1 = Lifter(name="John Doe", gender="Male", lifter_id_number="JD001", actual_weight=82.5, birth_date=date(2000, 5, 10))
        db.session.add(lifter1)
        db.session.commit() # Commit to get ID for primary class assignment
        lifter1.assign_primary_classes() # Assign classes after lifter is in session
        db.session.commit()

        lifter2 = Lifter(name="Jane Smith", gender="Female", lifter_id_number="JS002", actual_weight=68.0, birth_date=date(2002, 1, 15))
        db.session.add(lifter2)
        db.session.commit()
        lifter2.assign_primary_classes()
        db.session.commit()

        lifter3 = Lifter(name="Mike Johnson", gender="Male", lifter_id_number="MJ003", actual_weight=95.0, birth_date=date(1980, 11, 20))
        db.session.add(lifter3)
        db.session.commit()
        lifter3.assign_primary_classes()
        db.session.commit()
        # Add Mike to an additional age class (e.g., Open, if applicable)
        open_ac = AgeClass.query.filter_by(name="Open (24-39)").first()
        if open_ac:
            lifter3.additional_age_classes.append(open_ac)
            db.session.commit()


        lift_types = ['squat', 'bench', 'deadlift']
        opener_weights_map = {
            "JD001": {'squat': 180.0, 'bench': 110.0, 'deadlift': 200.0},
            "JS002": {'squat': 100.0, 'bench': 60.0, 'deadlift': 120.0},
            "MJ003": {'squat': 200.0, 'bench': 130.0, 'deadlift': 230.0}
        }

        for lifter in [lifter1, lifter2, lifter3]:
            opener_weights = opener_weights_map[lifter.lifter_id_number]
            for lift_type in lift_types:
                for i in range(1, 4): # 3 attempts for each lift type
                    new_lift_attempt = LiftAttempt(
                        lifter_id=lifter.id,
                        lift_type=lift_type,
                        weight_lifted=opener_weights[lift_type] + (i - 1) * 5, # Increment by 5kg for subsequent attempts
                        attempt_number=i,
                        status='pending'
                    )
                    db.session.add(new_lift_attempt)
            db.session.commit()
            print("Dummy lifters and attempts added.")
    else:
        print("Database tables already exist. Skipping creation and seeding.")


# --- API Endpoints ---

@app.route('/judge_login', methods=['POST'])
def judge_login():
    data = request.get_json()
    pin = data.get('pin')

    if not pin:
        return jsonify({"error": "PIN is required"}), 400

    judge_id = JUDGE_PINS.get(pin)
    if judge_id:
        return jsonify({"message": "Login successful", "judge_id": judge_id}), 200
    else:
        return jsonify({"error": "Invalid PIN"}), 401


@app.route('/meet_state', methods=['GET'])
def get_meet_state_endpoint():
    meet_state_obj = MeetState.query.get(1)
    if meet_state_obj:
        return jsonify(meet_state_obj.to_dict())
    return jsonify({"error": "Meet state not found"}), 404

@app.route('/meet_state', methods=['POST'])
def set_meet_state_endpoint():
    data = request.get_json()
    meet_state_obj = MeetState.query.get(1)
    if not meet_state_obj:
        return jsonify({"error": "Meet state not found"}), 404

    if 'current_lift_type' in data and data['current_lift_type'] in ['squat', 'bench', 'deadlift']:
        meet_state_obj.current_lift_type = data['current_lift_type']
        meet_state_obj.current_attempt_number = 1 
        meet_state_obj.current_active_lift_id = None
        db.session.commit()
        socketio.emit('meet_state_updated', meet_state_obj.to_dict())
        socketio.emit('active_lift_changed', None)
        return jsonify(meet_state_obj.to_dict()), 200
    return jsonify({"error": "Invalid or missing 'current_lift_type'."}), 400

@app.route('/meet_state/advance_attempt', methods=['POST'])
def advance_attempt_endpoint():
    meet_state_obj = MeetState.query.get(1)
    if not meet_state_obj:
        return jsonify({"error": "Meet state not found"}), 404

    if meet_state_obj.current_attempt_number < 3:
        meet_state_obj.current_attempt_number += 1
        meet_state_obj.current_active_lift_id = None
        db.session.commit()
        socketio.emit('meet_state_updated', meet_state_obj.to_dict())
        socketio.emit('active_lift_changed', None)
        return jsonify(meet_state_obj.to_dict()), 200
    return jsonify({"error": "Cannot advance past 3rd attempt."}), 400

@app.route('/weight_classes', methods=['GET'])
def get_weight_classes_endpoint():
    weight_classes = WeightClass.query.all()
    return jsonify([wc.to_dict() for wc in weight_classes])

@app.route('/weight_classes', methods=['POST'])
def add_weight_class_endpoint():
    data = request.get_json()
    name = data.get('name')
    min_weight = data.get('min_weight')
    max_weight = data.get('max_weight')
    gender = data.get('gender')

    if not all([name, min_weight is not None, gender]):
        return jsonify({"error": "Missing data for weight class"}), 400

    if WeightClass.query.filter_by(name=name).first():
        return jsonify({"error": f"Weight class '{name}' already exists"}), 409

    new_wc = WeightClass(name=name, min_weight=min_weight, max_weight=max_weight, gender=gender)
    db.session.add(new_wc)
    db.session.commit()
    all_lifters = Lifter.query.all()
    for lifter in all_lifters:
        lifter.assign_primary_classes()
    db.session.commit()
    socketio.emit('lifter_updated', None)
    return jsonify(new_wc.to_dict()), 201

@app.route('/weight_classes/<int:wc_id>', methods=['DELETE'])
def delete_weight_class_endpoint(wc_id):
    wc = WeightClass.query.get(wc_id)
    if not wc:
        return jsonify({"message": "Weight class not found"}), 404
    
    lifters_with_primary_wc = Lifter.query.filter_by(primary_weight_class_id=wc_id).all()
    if lifters_with_primary_wc:
        return jsonify({"error": "Cannot delete primary weight class with assigned lifters. Reassign lifters first."}), 409

    for lifter in Lifter.query.filter(Lifter.additional_weight_classes.any(WeightClass.id == wc_id)).all():
        lifter.additional_weight_classes.remove(wc)
    db.session.delete(wc)
    db.session.commit()
    socketio.emit('lifter_updated', None)
    return jsonify({"message": "Weight class deleted"}), 200

@app.route('/age_classes', methods=['GET'])
def get_age_classes_endpoint():
    age_classes = AgeClass.query.all()
    return jsonify([ac.to_dict() for ac in age_classes])

@app.route('/age_classes', methods=['POST'])
def add_age_class_endpoint():
    data = request.get_json()
    name = data.get('name')
    min_age = data.get('min_age')
    max_age = data.get('max_age')

    if not all([name, min_age is not None]):
        return jsonify({"error": "Missing data for age class"}), 400

    if AgeClass.query.filter_by(name=name).first():
        return jsonify({"error": f"Age class '{name}' already exists"}), 409

    new_ac = AgeClass(name=name, min_age=min_age, max_age=max_age)
    db.session.add(new_ac)
    db.session.commit()
    all_lifters = Lifter.query.all()
    for lifter in all_lifters:
        lifter.assign_primary_classes()
    db.session.commit()
    socketio.emit('lifter_updated', None)
    return jsonify(new_ac.to_dict()), 201

@app.route('/age_classes/<int:ac_id>', methods=['DELETE'])
def delete_age_class_endpoint(ac_id):
    ac = AgeClass.query.get(ac_id)
    if not ac:
        return jsonify({"message": "Age class not found"}), 404

    lifters_with_primary_ac = Lifter.query.filter_by(primary_age_class_id=ac_id).all()
    if lifters_with_primary_ac:
        return jsonify({"error": "Cannot delete primary age class with assigned lifters. Reassign lifters first."}), 409

    for lifter in Lifter.query.filter(Lifter.additional_age_classes.any(AgeClass.id == ac_id)).all():
        lifter.additional_age_classes.remove(ac)
    db.session.delete(ac)
    db.session.commit()
    socketio.emit('lifter_updated', None)
    return jsonify({"message": "Age class deleted"}), 200

@app.route('/lifters', methods=['GET'])
def get_lifters_endpoint():
    lifters = Lifter.query.all()
    return jsonify([l.to_dict() for l in lifters])

@app.route('/lifters', methods=['POST'])
def add_lifter_endpoint():
    data = request.get_json()
    name = data.get('name')
    gender = data.get('gender')
    lifter_id_number = data.get('lifter_id_number')
    actual_weight = data.get('actual_weight')
    birth_date_str = data.get('birth_date')
    opener_squat = data.get('opener_squat')
    opener_bench = data.get('opener_bench')
    opener_deadlift = data.get('opener_deadlift')

    if not all([name, gender, lifter_id_number, actual_weight is not None, birth_date_str,
                opener_squat is not None, opener_bench is not None, opener_deadlift is not None]):
        return jsonify({"error": "Missing data for lifter or openers"}), 400

    if Lifter.query.filter_by(lifter_id_number=lifter_id_number).first():
        return jsonify({"error": f"Lifter with ID '{lifter_id_number}' already exists"}), 409

    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid birth_date format. Use %Y-%m-%d."}), 400

    new_lifter = Lifter(
        name=name,
        gender=gender,
        lifter_id_number=lifter_id_number,
        actual_weight=actual_weight,
        birth_date=birth_date
    )
    db.session.add(new_lifter)
    db.session.commit()

    new_lifter.assign_primary_classes()
    db.session.commit()

    lift_types = ['squat', 'bench', 'deadlift']
    opener_weights = {
        'squat': opener_squat,
        'bench': opener_bench,
        'deadlift': opener_deadlift
    }

    for lift_type in lift_types:
        for i in range(1, 4):
            initial_weight = opener_weights[lift_type] + (i - 1) * 5
            new_lift_attempt = LiftAttempt(
                lifter_id=new_lifter.id,
                lift_type=lift_type,
                weight_lifted=initial_weight,
                attempt_number=i,
                status='pending'
            )
            db.session.add(new_lift_attempt)
    db.session.commit()

    socketio.emit('lifter_added', new_lifter.to_dict())
    return jsonify(new_lifter.to_dict()), 201

@app.route('/lifters/<int:lifter_id>/add_additional_weight_class', methods=['POST'])
def add_additional_weight_class(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"error": "Lifter not found"}), 404
    data = request.get_json()
    weight_class_id = data.get('weight_class_id')
    wc = WeightClass.query.get(weight_class_id)

    if not wc:
        return jsonify({"error": "Weight class not found"}), 404

    if lifter.primary_weight_class_id == wc.id:
        return jsonify({"error": "Cannot add primary weight class as an additional class."}), 400

    if lifter.primary_weight_class and wc.min_weight < lifter.primary_weight_class.min_weight:
        return jsonify({"error": "Additional weight class must be strictly heavier or equal to the primary class."}), 400

    if wc not in lifter.additional_weight_classes:
        lifter.additional_weight_classes.append(wc)
        db.session.commit()
        socketio.emit('lifter_updated', lifter.to_dict())
        return jsonify(lifter.to_dict()), 200
    return jsonify({"message": "Weight class already added to this lifter."}), 409

@app.route('/lifters/<int:lifter_id>/remove_additional_weight_class', methods=['POST'])
def remove_additional_weight_class(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"error": "Lifter not found"}), 404
    data = request.get_json()
    weight_class_id = data.get('weight_class_id')
    wc = WeightClass.query.get(weight_class_id)

    if not wc:
        return jsonify({"error": "Weight class not found"}), 404

    if wc in lifter.additional_weight_classes:
        lifter.additional_weight_classes.remove(wc)
        db.session.commit()
        socketio.emit('lifter_updated', lifter.to_dict())
        return jsonify(lifter.to_dict()), 200
    return jsonify({"message": "Weight class not found in additional classes for this lifter."}), 404

@app.route('/lifters/<int:lifter_id>/add_additional_age_class', methods=['POST'])
def add_additional_age_class(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"error": "Lifter not found"}), 404
    data = request.get_json()
    age_class_id = data.get('age_class_id')
    ac = AgeClass.query.get(age_class_id)

    if not ac:
        return jsonify({"error": "Age class not found"}), 404

    if lifter.primary_age_class_id == ac.id:
        return jsonify({"error": "Cannot add primary age class as an additional class."}), 400
    
    if lifter.primary_age_class and ac.min_age < lifter.primary_age_class.min_age:
        return jsonify({"error": "Additional age class must be strictly older or equal to the primary class."}), 400

    if ac not in lifter.additional_age_classes:
        lifter.additional_age_classes.append(ac)
        db.session.commit()
        socketio.emit('lifter_updated', lifter.to_dict())
        return jsonify(lifter.to_dict()), 200
    return jsonify({"message": "Age class already added to this lifter."}), 409

@app.route('/lifters/<int:lifter_id>/remove_additional_age_class', methods=['POST'])
def remove_additional_age_class(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"error": "Lifter not found"}), 404
    data = request.get_json()
    age_class_id = data.get('age_class_id')
    ac = AgeClass.query.get(age_class_id)

    if not ac:
        return jsonify({"error": "Age class not found"}), 404

    if ac in lifter.additional_age_classes:
        lifter.additional_age_classes.remove(ac)
        db.session.commit()
        socketio.emit('lifter_updated', lifter.to_dict())
        return jsonify(lifter.to_dict()), 200
    return jsonify({"message": "Age class not found in additional classes for this lifter."}), 404


@app.route('/lifts', methods=['GET'])
def get_lifts():
    lifts = LiftAttempt.query.order_by(LiftAttempt.timestamp.asc()).all()
    return jsonify([lift.to_dict() for lift in lifts])

@app.route('/current_lift', methods=['GET'])
def get_current_lift_endpoint():
    meet_state_obj = MeetState.query.get(1)
    if meet_state_obj and meet_state_obj.current_active_lift_id:
        active_lift = LiftAttempt.query.get(meet_state_obj.current_active_lift_id)
        if active_lift:
            return jsonify(active_lift.to_dict())
    return jsonify({"message": "No active lift"}), 404

@app.route('/set_active_lift', methods=['POST'])
def set_active_lift_endpoint():
    data = request.get_json()
    lift_id = data.get('lift_id')

    meet_state_obj = MeetState.query.get(1)
    if not meet_state_obj:
        return jsonify({"error": "Meet state not found"}), 404

    # Deactivate any currently active lift
    if meet_state_obj.current_active_lift_id:
        current_active = LiftAttempt.query.get(meet_state_obj.current_active_lift_id)
        if current_active:
            if current_active.overall_result is None:
                current_active.status = 'pending'
            else:
                current_active.status = 'completed'
            db.session.commit()
            socketio.emit('lift_updated', current_active.to_dict())

    new_active = None
    if lift_id:
        new_active = LiftAttempt.query.filter_by(
            id=lift_id,
            status='pending',
            lift_type=meet_state_obj.current_lift_type,
            attempt_number=meet_state_obj.current_attempt_number
        ).first()
        if not new_active:
            return jsonify({"error": "Lift not found or not in pending status for current type/attempt."}), 404
    else:
        # Auto-select next pending lift
        new_active = LiftAttempt.query.join(Lifter).filter(
            LiftAttempt.status == 'pending',
            LiftAttempt.lift_type == meet_state_obj.current_lift_type,
            LiftAttempt.attempt_number == meet_state_obj.current_attempt_number
        ).order_by(
            LiftAttempt.weight_lifted.asc(),
            Lifter.actual_weight.asc(),
            LiftAttempt.timestamp.asc()
        ).first()
        if not new_active:
            meet_state_obj.current_active_lift_id = None
            db.session.commit()
            socketio.emit('meet_state_updated', meet_state_obj.to_dict())
            socketio.emit('active_lift_changed', None)
            return jsonify({"message": "No pending lifts in current queue."}), 200

    new_active.status = 'active'
    new_active.judge1_score = None
    new_active.judge2_score = None
    new_active.judge3_score = None
    new_active.overall_result = None
    db.session.commit()

    meet_state_obj.current_active_lift_id = new_active.id
    db.session.commit()

    socketio.emit('active_lift_changed', new_active.to_dict())
    socketio.emit('lift_updated', new_active.to_dict())
    socketio.emit('meet_state_updated', meet_state_obj.to_dict())
    return jsonify(new_active.to_dict())

@app.route('/submit_score', methods=['POST'])
def submit_score_endpoint():
    data = request.get_json()
    lift_id = data.get('lift_id')
    judge_number = data.get('judge_number')
    score = data.get('score')

    if not all([lift_id, judge_number, score is not None]):
        return jsonify({"error": "Missing data"}), 400

    lift = LiftAttempt.query.get(lift_id)
    if not lift:
        return jsonify({"error": "Lift not found"}), 404

    meet_state_obj = MeetState.query.get(1)
    if not meet_state_obj or meet_state_obj.current_active_lift_id != lift.id:
        return jsonify({"error": "This is not the current active lift."}), 400

    try:
        if judge_number == 1:
            lift.judge1_score = score
        elif judge_number == 2:
            lift.judge2_score = score
        elif judge_number == 3:
            lift.judge3_score = score
        else:
            return jsonify({"error": "Invalid judge number"}), 400

        db.session.commit()

        if lift.calculate_overall_result():
            db.session.commit()
            if lift.overall_result is not None:
                lift.status = 'completed'
                db.session.commit()
                if meet_state_obj.current_active_lift_id == lift.id:
                    meet_state_obj.current_active_lift_id = None
                    db.session.commit()
                    socketio.emit('meet_state_updated', meet_state_obj.to_dict())

            socketio.emit('lift_updated', lift.to_dict())
            return jsonify(lift.to_dict())

        socketio.emit('lift_updated', lift.to_dict())
        return jsonify(lift.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/lifters/<int:lifter_id>/attempts', methods=['GET'])
def get_lifter_attempts_endpoint(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"message": "Lifter not found"}), 404
    
    attempts = LiftAttempt.query.filter_by(lifter_id=lifter_id).order_by(
        LiftAttempt.lift_type, LiftAttempt.attempt_number
    ).all()
    
    return jsonify([att.to_dict() for att in attempts])

@app.route('/rankings', methods=['GET'])
def get_rankings_endpoint():
    all_lifters = Lifter.query.all()
    rankings_by_class = {}

    for lifter in all_lifters:
        completed_attempts = LiftAttempt.query.filter_by(
            lifter_id=lifter.id,
            status='completed',
            overall_result=True
        ).all()

        best_squat = 0.0
        best_bench = 0.0
        best_deadlift = 0.0

        for attempt in completed_attempts:
            if attempt.lift_type == 'squat':
                best_squat = max(best_squat, attempt.weight_lifted)
            elif attempt.lift_type == 'bench':
                best_bench = max(best_bench, attempt.weight_lifted)
            elif attempt.lift_type == 'deadlift':
                best_deadlift = max(best_deadlift, attempt.weight_lifted)
        
        total = best_squat + best_bench + best_deadlift

        lifter_data = {
            'id': lifter.id,
            'name': lifter.name,
            'lifter_id_number': lifter.lifter_id_number,
            'gender': lifter.gender,
            'actual_weight': lifter.actual_weight,
            'age': lifter.calculate_age(),
            'best_squat': best_squat if best_squat > 0 else 'N/A',
            'best_bench': best_bench if best_bench > 0 else 'N/A',
            'best_deadlift': best_deadlift if best_deadlift > 0 else 'N/A',
            'total': total if total > 0 else 'N/A',
            'primary_weight_class_name': lifter.primary_weight_class.name if lifter.primary_weight_class else 'N/A',
            'primary_age_class_name': lifter.primary_age_class.name if lifter.primary_age_class else 'N/A',
            'additional_weight_class_names': [wc.name for wc in lifter.additional_weight_classes],
            'additional_age_class_names': [ac.name for ac in lifter.additional_age_classes],
        }

        all_relevant_weight_classes = [lifter.primary_weight_class] + list(lifter.additional_weight_classes)
        for wc in all_relevant_weight_classes:
            if wc:
                wc_key = wc.name
                if wc_key not in rankings_by_class:
                    rankings_by_class[wc_key] = []
                rankings_by_class[wc_key].append(lifter_data)
        
        all_relevant_age_classes = [lifter.primary_age_class] + list(lifter.additional_age_classes)
        for ac in all_relevant_age_classes:
            if ac:
                ac_key = ac.name
                if ac_key not in rankings_by_class:
                    rankings_by_class[ac_key] = []
                if not any(l['id'] == lifter_data['id'] for l in rankings_by_class[ac_key]):
                    rankings_by_class[ac_key].append(lifter_data)

    for class_key in rankings_by_class:
        rankings_by_class[class_key].sort(key=lambda x: x['total'] if isinstance(x['total'], (int, float)) else -1, reverse=True)

    return jsonify(rankings_by_class)

@app.route('/next_lift_in_queue', methods=['GET'])
def get_next_lift_in_queue_endpoint():
    meet_state_obj = MeetState.query.get(1)
    if not meet_state_obj:
        return jsonify({"error": "Meet state not found"}), 404

    next_lift = LiftAttempt.query.join(Lifter).filter(
        LiftAttempt.status == 'pending',
        LiftAttempt.lift_type == meet_state_obj.current_lift_type,
        LiftAttempt.attempt_number == meet_state_obj.current_attempt_number
    ).order_by(
        LiftAttempt.weight_lifted.asc(),
        Lifter.actual_weight.asc(),
        LiftAttempt.timestamp.asc()
    ).first()
    
    if next_lift:
        return jsonify(next_lift.to_dict())
    return jsonify({"message": "No pending lifts in current queue for this lift type."}), 404

@app.route('/export_meet_data', methods=['GET'])
def export_meet_data_endpoint():
    try:
        backup_dir = os.path.join(basedir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"powerlifting_meet_data_{timestamp_str}.xlsx"
        file_path = os.path.join(backup_dir, file_name)

        lifters_data_list = []
        for lifter in Lifter.query.all():
            lifter_dict = lifter.to_dict()
            lifter_dict['best_squat'] = 'N/A'
            lifter_dict['best_bench'] = 'N/A'
            lifter_dict['best_deadlift'] = 'N/A'
            lifter_dict['total'] = 'N/A'

            best_lifts = {}
            for attempt in LiftAttempt.query.filter_by(lifter_id=lifter.id, overall_result=True, status='completed').all():
                best_lifts[attempt.lift_type] = max(best_lifts.get(attempt.lift_type, 0), attempt.weight_lifted)

            if 'squat' in best_lifts: lifter_dict['best_squat'] = best_lifts['squat']
            if 'bench' in best_lifts: lifter_dict['best_bench'] = best_lifts['bench']
            if 'deadlift' in best_lifts: lifter_dict['best_deadlift'] = best_lifts['deadlift']
            
            total_sum = (best_lifts.get('squat', 0) or 0) + \
                        (best_lifts.get('bench', 0) or 0) + \
                        (best_lifts.get('deadlift', 0) or 0)
            if total_sum > 0: lifter_dict['total'] = total_sum

            lifter_dict['additional_weight_classes'] = ', '.join(lifter_dict['additional_weight_class_names'])
            lifter_dict['additional_age_classes'] = ', '.join(lifter_dict['additional_age_class_names'])
            
            del lifter_dict['additional_weight_class_names']
            del lifter_dict['additional_age_class_names']
            del lifter_dict['additional_weight_class_ids']
            del lifter_dict['additional_age_class_ids']

            lifters_data_list.append(lifter_dict)
        
        lifts_data_list = []
        for lift in LiftAttempt.query.all():
            lift_dict = lift.to_dict()
            lift_dict['judge1_score'] = 'GOOD' if lift_dict['judge1_score'] else ('BAD' if lift_dict['judge1_score'] is not None else 'N/A')
            lift_dict['judge2_score'] = 'GOOD' if lift_dict['judge2_score'] else ('BAD' if lift_dict['judge2_score'] is not None else 'N/A')
            lift_dict['judge3_score'] = 'GOOD' if lift_dict['judge3_score'] else ('BAD' if lift_dict['judge3_score'] is not None else 'N/A')
            lift_dict['overall_result'] = 'GOOD LIFT' if lift_dict['overall_result'] else ('NO LIFT' if lift_dict['overall_result'] is not None else 'PENDING')
            lifts_data_list.append(lift_dict)


        df_lifters = pd.DataFrame(lifters_data_list)
        df_lifts = pd.DataFrame(lifts_data_list)
        df_weight_classes = pd.DataFrame([wc.to_dict() for wc in WeightClass.query.all()])
        df_age_classes = pd.DataFrame([ac.to_dict() for ac in AgeClass.query.all()])
        df_meet_state = pd.DataFrame([MeetState.query.get(1).to_dict()])

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df_lifters.to_excel(writer, sheet_name='Lifters', index=False)
            df_lifts.to_excel(writer, sheet_name='Lift Attempts', index=False)
            df_weight_classes.to_excel(writer, sheet_name='WeightClasses', index=False)
            df_age_classes.to_excel(writer, sheet_name='AgeClasses', index=False)
            df_meet_state.to_excel(writer, sheet_name='MeetState', index=False)
        
        return jsonify({"message": f"Meet data exported successfully to {file_path}", "file_path": file_path}), 200

    except Exception as e:
        app.logger.error(f"Error during Excel export: {e}")
        return jsonify({"error": f"Failed to export data: {str(e)}"}), 500

# --- Socket.IO Events ---
@socketio.on('connect')
def test_connect():
    print('Client connected')
    meet_state_obj = MeetState.query.get(1)
    if meet_state_obj:
        emit('meet_state_updated', meet_state_obj.to_dict())

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
