# Backend/app.py

# IMPORTANT: eventlet.monkey_patch() MUST be called BEFORE any other imports
# that might use standard library modules (like socket, threading).
import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import random
from datetime import datetime, date

# Initialize Flask app
app = Flask(__name__)

# Configure CORS to allow requests from ANY origin.
# !!! IMPORTANT: This is for debugging purposes ONLY. For production,
# !!! you should restrict this to your actual frontend URL(s).
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Add connection pooling options for resilience
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,  # Test connections before use
    "pool_recycle": 3600,   # Recycle connections after 1 hour (common for cloud DBs)
    "pool_timeout": 30,     # Max wait for a connection from the pool (seconds)
}
db = SQLAlchemy(app)

# Initialize SocketIO with explicit CORS configuration for ANY origin.
# !!! IMPORTANT: This is for debugging purposes ONLY. For production,
# !!! you should restrict this to your actual frontend URL(s).
socketio = SocketIO(app, cors_allowed_origins="*")

# Explicitly register a teardown function for the database session
@app.teardown_appcontext
def remove_session(exception=None):
    db.session.remove()

# Example: Judge PINs (replace with secure storage in production)
JUDGE_PINS = {
    "1111": "Judge 1",
    "2222": "Judge 2",
    "3333": "Judge 3",
}

# Helper function to calculate age
def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

# --- Database Models ---
class MeetState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_lift_type = db.Column(db.String(50), default='squat') # squat, bench, deadlift
    current_attempt_number = db.Column(db.Integer, default=1) # 1, 2, 3
    current_active_lift_id = db.Column(db.Integer, db.ForeignKey('lift.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'current_lift_type': self.current_lift_type,
            'current_attempt_number': self.current_attempt_number,
            'current_active_lift_id': self.current_active_lift_id
        }

class Lifter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False) # Male, Female
    lifter_id_number = db.Column(db.String(50), unique=True, nullable=False)
    actual_weight = db.Column(db.Float, nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    opener_squat = db.Column(db.Float, nullable=True)
    opener_bench = db.Column(db.Float, nullable=True)
    opener_deadlift = db.Column(db.Float, nullable=True)

    primary_weight_class_id = db.Column(db.Integer, db.ForeignKey('weight_class.id'), nullable=True)
    primary_age_class_id = db.Column(db.Integer, db.ForeignKey('age_class.id'), nullable=True)

    # Relationships for easier access in Python
    primary_weight_class = db.relationship('WeightClass', foreign_keys=[primary_weight_class_id])
    primary_age_class = db.relationship('AgeClass', foreign_keys=[primary_age_class_id])

    # Many-to-many for additional classes using association tables
    additional_weight_classes = db.relationship('WeightClass', secondary='lifter_additional_weight_class',
                                                backref=db.backref('additional_lifters_wc', lazy='dynamic'))
    additional_age_classes = db.relationship('AgeClass', secondary='lifter_additional_age_class',
                                             backref=db.backref('additional_lifters_ac', lazy='dynamic'))

    lifts = db.relationship('Lift', backref='lifter', lazy=True)

    def to_dict(self):
        age = calculate_age(self.birth_date)
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'lifter_id_number': self.lifter_id_number,
            'actual_weight': self.actual_weight,
            'birth_date': self.birth_date.isoformat(),
            'age': age,
            'opener_squat': self.opener_squat,
            'opener_bench': self.opener_bench,
            'opener_deadlift': self.opener_deadlift,
            'primary_weight_class_id': self.primary_weight_class_id,
            'primary_weight_class_name': self.primary_weight_class.name if self.primary_weight_class else None,
            'primary_age_class_id': self.primary_age_class_id,
            'primary_age_class_name': self.primary_age_class.name if self.primary_age_class else None,
            'additional_weight_class_ids': [wc.id for wc in self.additional_weight_classes],
            'additional_weight_class_names': [wc.name for wc in self.additional_weight_classes],
            'additional_age_class_ids': [ac.id for ac in self.additional_age_classes],
            'additional_age_class_names': [ac.name for ac in self.additional_age_classes],
        }

class WeightClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    min_weight = db.Column(db.Float, nullable=False)
    max_weight = db.Column(db.Float, nullable=True) # Max weight can be null for open classes
    gender = db.Column(db.String(10), nullable=False) # Male, Female, Both

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'min_weight': self.min_weight,
            'max_weight': self.max_weight,
            'gender': self.gender
        }

class AgeClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    min_age = db.Column(db.Integer, nullable=False)
    max_age = db.Column(db.Integer, nullable=True) # Max age can be null for open classes

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'min_age': self.min_age,
            'max_age': self.max_age
        }

# Association tables for many-to-many relationships
lifter_additional_weight_class = db.Table('lifter_additional_weight_class',
    db.Column('lifter_id', db.Integer, db.ForeignKey('lifter.id'), primary_key=True),
    db.Column('weight_class_id', db.Integer, db.ForeignKey('weight_class.id'), primary_key=True)
)

lifter_additional_age_class = db.Table('lifter_additional_age_class',
    db.Column('lifter_id', db.Integer, db.ForeignKey('lifter.id'), primary_key=True),
    db.Column('age_class_id', db.Integer, db.ForeignKey('age_class.id'), primary_key=True)
)

class Lift(db.Model):
    __tablename__ = 'lift' # Explicitly set table name for clarity
    id = db.Column(db.Integer, primary_key=True)
    lifter_id = db.Column(db.Integer, db.ForeignKey('lifter.id'), nullable=False)
    lift_type = db.Column(db.String(50), nullable=False) # squat, bench, deadlift
    attempt_number = db.Column(db.Integer, nullable=False) # 1, 2, 3
    weight_lifted = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending') # pending, active, completed

    judge1_score = db.Column(db.Boolean, nullable=True)
    judge2_score = db.Column(db.Boolean, nullable=True)
    judge3_score = db.Column(db.Boolean, nullable=True)
    overall_result = db.Column(db.Boolean, nullable=True) # True for good lift, False for no lift

    def to_dict(self):
        return {
            'id': self.id,
            'lifter_id': self.lifter_id,
            'lifter_name': self.lifter.name,
            'lifter_id_number': self.lifter.lifter_id_number,
            'gender': self.lifter.gender,
            'weight_class_name': self.lifter.primary_weight_class.name if self.lifter.primary_weight_class else None,
            'lift_type': self.lift_type,
            'attempt_number': self.attempt_number,
            'weight_lifted': self.weight_lifted,
            'status': self.status,
            'judge1_score': self.judge1_score,
            'judge2_score': self.judge2_score,
            'judge3_score': self.judge3_score,
            'overall_result': self.overall_result
        }

# --- Helper Functions (Backend Logic) ---
def assign_primary_classes(lifter):
    """Assigns primary weight and age classes to a lifter."""
    # Assign Primary Weight Class
    weight_class = WeightClass.query.filter(
        (WeightClass.min_weight <= lifter.actual_weight) &
        ((WeightClass.max_weight >= lifter.actual_weight) | (WeightClass.max_weight.is_(None))) &
        ((WeightClass.gender == lifter.gender) | (WeightClass.gender == 'Both'))
    ).order_by(WeightClass.min_weight).first()

    if weight_class:
        lifter.primary_weight_class_id = weight_class.id
    else:
        lifter.primary_weight_class_id = None # Or assign a default/error class

    # Assign Primary Age Class
    age = calculate_age(lifter.birth_date)
    age_class = AgeClass.query.filter(
        (AgeClass.min_age <= age) &
        ((AgeClass.max_age >= age) | (AgeClass.max_age.is_(None)))
    ).order_by(AgeClass.min_age).first()

    if age_class:
        lifter.primary_age_class_id = age_class.id
    else:
        lifter.primary_age_class_id = None # Or assign a default/error class
    db.session.add(lifter)
    db.session.commit()

def generate_lifts_for_lifter(lifter):
    """Generates 3 lifts for each lift type for a new lifter."""
    lifts_to_add = []
    for lift_type_name in ['squat', 'bench', 'deadlift']:
        opener_weight = getattr(lifter, f'opener_{lift_type_name}')
        if opener_weight is not None:
            lifts_to_add.append(Lift(
                lifter_id=lifter.id,
                lift_type=lift_type_name,
                attempt_number=1,
                weight_lifted=opener_weight
            ))
            # Attempt 2: Opener + 5kg
            lifts_to_add.append(Lift(
                lifter_id=lifter.id,
                lift_type=lift_type_name,
                attempt_number=2,
                weight_lifted=opener_weight + 5
            ))
            # Attempt 3: Opener + 10kg (or a smart increment)
            lifts_to_add.append(Lift(
                lifter_id=lifter.id,
                lift_type=lift_type_name,
                attempt_number=3,
                weight_lifted=opener_weight + 10
            ))
    db.session.add_all(lifts_to_add)
    db.session.commit()

def update_overall_result(lift):
    """Updates the overall result of a lift based on judge scores."""
    scores = [lift.judge1_score, lift.judge2_score, lift.judge3_score]
    # Filter out None scores (judges who haven't scored yet)
    valid_scores = [s for s in scores if s is not None]

    if len(valid_scores) >= 2: # At least two judges must have scored
        good_lifts = valid_scores.count(True)
        no_lifts = valid_scores.count(False)
        if good_lifts > no_lifts:
            lift.overall_result = True
            lift.status = 'completed'
        elif no_lifts > good_lifts:
            lift.overall_result = False
            lift.status = 'completed'
        db.session.commit()
        socketio.emit('lift_updated', lift.to_dict()) # Emit update
        return True
    return False


# --- Routes ---
@app.route('/')
def index():
    return "Powerlifting Meet Backend is running!"

# Meet State Management
@app.route('/meet_state', methods=['GET', 'POST'])
def manage_meet_state():
    meet_state = MeetState.query.first()
    if not meet_state:
        meet_state = MeetState()
        db.session.add(meet_state)
        db.session.commit()

    if request.method == 'POST':
        data = request.get_json()
        if 'current_lift_type' in data:
            meet_state.current_lift_type = data['current_lift_type']
            meet_state.current_attempt_number = 1 # Reset attempt when lift type changes
            meet_state.current_active_lift_id = None # Clear active lift
        db.session.commit()
        socketio.emit('meet_state_updated', meet_state.to_dict())
        return jsonify(meet_state.to_dict())
    return jsonify(meet_state.to_dict())

@app.route('/meet_state/advance_attempt', methods=['POST'])
def advance_attempt_route():
    meet_state = MeetState.query.first()
    if not meet_state:
        return jsonify({"error": "Meet state not initialized"}), 404

    if meet_state.current_attempt_number < 3:
        meet_state.current_attempt_number += 1
        meet_state.current_active_lift_id = None # Clear active lift when advancing attempt
        db.session.commit()
        socketio.emit('meet_state_updated', meet_state.to_dict())
        return jsonify(meet_state.to_dict())
    else:
        return jsonify({"error": "Cannot advance beyond attempt 3"}), 400

@app.route('/set_active_lift', methods=['POST'])
def set_active_lift():
    data = request.get_json()
    lift_id = data.get('lift_id')

    meet_state = MeetState.query.first()
    if not meet_state:
        return jsonify({"error": "Meet state not initialized"}), 404

    # If no lift_id is provided, auto-select the next pending lift
    if lift_id is None:
        next_lift_candidate = Lift.query.filter_by(
            status='pending',
            lift_type=meet_state.current_lift_type,
            attempt_number=meet_state.current_attempt_number
        ).order_by(Lift.weight_lifted, Lift.lifter_id).first() # Order to pick consistently
        if next_lift_candidate:
            lift_id = next_lift_candidate.id
        else:
            meet_state.current_active_lift_id = None
            db.session.commit()
            socketio.emit('active_lift_changed', None) # No active lift
            return jsonify({"message": "No more pending lifts for current attempt/type. Active lift cleared."}), 200

    lift = Lift.query.get(lift_id)
    if not lift:
        return jsonify({"error": "Lift not found"}), 404
    if lift.status != 'pending':
        return jsonify({"error": "Only pending lifts can be set as active"}), 400

    # Set any previous active lift back to pending (if not completed)
    if meet_state.current_active_lift_id:
        prev_active_lift = Lift.query.get(meet_state.current_active_lift_id)
        if prev_active_lift and prev_active_lift.status == 'active':
            prev_active_lift.status = 'pending'
            db.session.add(prev_active_lift)
            socketio.emit('lift_updated', prev_active_lift.to_dict())

    meet_state.current_active_lift_id = lift.id
    lift.status = 'active'
    lift.judge1_score = None # Reset scores for new active lift
    lift.judge2_score = None
    lift.judge3_score = None
    lift.overall_result = None

    db.session.add_all([meet_state, lift])
    db.session.commit()

    socketio.emit('active_lift_changed', lift.to_dict())
    return jsonify(lift.to_dict())

@app.route('/current_lift', methods=['GET'])
def get_current_lift():
    meet_state = MeetState.query.first()
    if meet_state and meet_state.current_active_lift_id:
        lift = Lift.query.get(meet_state.current_active_lift_id)
        if lift:
            return jsonify(lift.to_dict())
    return jsonify({}), 200 # Return empty object if no current lift

@app.route('/next_lift_in_queue', methods=['GET'])
def get_next_lift_in_queue():
    # This endpoint now primarily serves to trigger queue updates, but the queue itself
    # is typically calculated and fetched by the frontend based on all lifts.
    # We ensure current meet state is fetched for consistent filtering logic.
    meet_state = MeetState.query.first()
    if not meet_state:
        return jsonify({"message": "Meet state not initialized"}), 200

    # Frontend will query /lifts and filter, so no need to return a specific "next" lift here.
    # This endpoint can be used to signal updates if complex queueing logic happens on backend.
    return jsonify({"message": "Queue calculation handled by frontend, data from /lifts"}), 200

# Lifter Management
@app.route('/lifters', methods=['GET', 'POST'])
def manage_lifters():
    if request.method == 'POST':
        data = request.get_json()
        new_lifter = Lifter(
            name=data['name'],
            gender=data['gender'],
            lifter_id_number=data['lifter_id_number'],
            actual_weight=data['actual_weight'],
            birth_date=datetime.strptime(data['birth_date'], '%Y-%m-%d').date(),
            opener_squat=data.get('opener_squat'),
            opener_bench=data.get('opener_bench'),
            opener_deadlift=data.get('opener_deadlift')
        )
        db.session.add(new_lifter)
        db.session.commit()
        assign_primary_classes(new_lifter)
        generate_lifts_for_lifter(new_lifter)
        socketio.emit('lifter_added', new_lifter.to_dict()) # Emit lifter added event
        return jsonify(new_lifter.to_dict()), 201
    elif request.method == 'GET':
        lifters = Lifter.query.all()
        return jsonify([lifter.to_dict() for lifter in lifters])

@app.route('/lifters/<int:lifter_id>/add_additional_weight_class', methods=['POST'])
def add_lifter_additional_weight_class(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"error": "Lifter not found"}), 404
    data = request.get_json()
    weight_class_id = data.get('weight_class_id')
    weight_class = WeightClass.query.get(weight_class_id)
    if not weight_class:
        return jsonify({"error": "Weight class not found"}), 404

    if weight_class not in lifter.additional_weight_classes:
        lifter.additional_weight_classes.append(weight_class)
        db.session.commit()
        socketio.emit('lifter_updated', lifter.to_dict())
        return jsonify(lifter.to_dict()), 200
    return jsonify({"message": "Weight class already added"}), 409

@app.route('/lifters/<int:lifter_id>/remove_additional_weight_class', methods=['POST'])
def remove_lifter_additional_weight_class(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"error": "Lifter not found"}), 404
    data = request.get_json()
    weight_class_id = data.get('weight_class_id')
    weight_class = WeightClass.query.get(weight_class_id)
    if not weight_class:
        return jsonify({"error": "Weight class not found"}), 404

    if weight_class in lifter.additional_weight_classes:
        lifter.additional_weight_classes.remove(weight_class)
        db.session.commit()
        socketio.emit('lifter_updated', lifter.to_dict())
        return jsonify(lifter.to_dict()), 200
    return jsonify({"message": "Weight class not found on lifter"}), 404

@app.route('/lifters/<int:lifter_id>/add_additional_age_class', methods=['POST'])
def add_lifter_additional_age_class(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"error": "Lifter not found"}), 404
    data = request.get_json()
    age_class_id = data.get('age_class_id')
    age_class = AgeClass.query.get(age_class_id)
    if not age_class:
        return jsonify({"error": "Age class not found"}), 404

    if age_class not in lifter.additional_age_classes:
        lifter.additional_age_classes.append(age_class)
        db.session.commit()
        socketio.emit('lifter_updated', lifter.to_dict())
        return jsonify(lifter.to_dict()), 200
    return jsonify({"message": "Age class already added"}), 409

@app.route('/lifters/<int:lifter_id>/remove_additional_age_class', methods=['POST'])
def remove_lifter_additional_age_class(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"error": "Lifter not found"}), 404
    data = request.get_json()
    age_class_id = data.get('age_class_id')
    age_class = AgeClass.query.get(age_class_id)
    if not age_class:
        return jsonify({"error": "Age class not found"}), 404

    if age_class in lifter.additional_age_classes:
        lifter.additional_age_classes.remove(age_class)
        db.session.commit()
        socketio.emit('lifter_updated', lifter.to_dict())
        return jsonify(lifter.to_dict()), 200
    return jsonify({"message": "Age class not found on lifter"}), 404

# Class Management
@app.route('/weight_classes', methods=['GET', 'POST'])
def manage_weight_classes():
    if request.method == 'POST':
        data = request.get_json()
        new_wc = WeightClass(
            name=data['name'],
            min_weight=data['min_weight'],
            max_weight=data.get('max_weight'),
            gender=data['gender']
        )
        db.session.add(new_wc)
        db.session.commit()
        all_lifters = Lifter.query.all()
        for lifter in all_lifters:
            assign_primary_classes(lifter)
        socketio.emit('weight_class_updated', new_wc.to_dict())
        socketio.emit('lifter_updated', None)
        return jsonify(new_wc.to_dict()), 201
    elif request.method == 'GET':
        wcs = WeightClass.query.all()
        return jsonify([wc.to_dict() for wc in wcs])

@app.route('/weight_classes/<int:wc_id>', methods=['DELETE'])
def delete_weight_class(wc_id):
    wc = WeightClass.query.get(wc_id)
    if not wc:
        return jsonify({"error": "Weight class not found"}), 404
    db.session.delete(wc)
    db.session.commit()
    all_lifters = Lifter.query.all()
    for lifter in all_lifters:
        assign_primary_classes(lifter)
    socketio.emit('weight_class_updated', None)
    socketio.emit('lifter_updated', None)
    return jsonify({"message": "Weight class deleted"}), 200

@app.route('/age_classes', methods=['GET', 'POST'])
def manage_age_classes():
    if request.method == 'POST':
        data = request.get_json()
        new_ac = AgeClass(
            name=data['name'],
            min_age=data['min_age'],
            max_age=data.get('max_age')
        )
        db.session.add(new_ac)
        db.session.commit()
        all_lifters = Lifter.query.all()
        for lifter in all_lifters:
            assign_primary_classes(lifter)
        socketio.emit('age_class_updated', new_ac.to_dict())
        socketio.emit('lifter_updated', None)
        return jsonify(new_ac.to_dict()), 201
    elif request.method == 'GET':
        acs = AgeClass.query.all()
        return jsonify([ac.to_dict() for ac in acs])

@app.route('/age_classes/<int:ac_id>', methods=['DELETE'])
def delete_age_class(ac_id):
    ac = AgeClass.query.get(ac_id)
    if not ac:
        return jsonify({"error": "Age class not found"}), 404
    db.session.delete(ac)
    db.session.commit()
    all_lifters = Lifter.query.all()
    for lifter in all_lifters:
        assign_primary_classes(lifter)
    socketio.emit('age_class_updated', None)
    socketio.emit('lifter_updated', None)
    return jsonify({"message": "Age class deleted"}), 200

# Lift scoring
@app.route('/lifts', methods=['GET'])
def get_all_lifts():
    lifts = Lift.query.all()
    return jsonify([lift.to_dict() for lift in lifts])

@app.route('/lifts/<int:lift_id>/score', methods=['POST'])
def score_lift(lift_id):
    lift = Lift.query.get(lift_id)
    if not lift:
        return jsonify({"error": "Lift not found"}), 404

    data = request.get_json()
    judge_pin = data.get('judge_pin')
    score = data.get('score')

    if judge_pin not in JUDGE_PINS:
        return jsonify({"error": "Invalid Judge PIN"}), 403

    judge_name = JUDGE_PINS[judge_pin]

    if judge_name == "Judge 1":
        lift.judge1_score = score
    elif judge_name == "Judge 2":
        lift.judge2_score = score
    elif judge_name == "Judge 3":
        lift.judge3_score = score
    else:
        return jsonify({"error": "Judge not recognized"}), 400

    db.session.commit()
    update_overall_result(lift)
    socketio.emit('lift_updated', lift.to_dict())
    return jsonify(lift.to_dict())

# Data Export
@app.route('/export_meet_data', methods=['GET'])
def export_meet_data():
    try:
        lifters = Lifter.query.all()
        lifts = Lift.query.all()

        lifters_csv = "Lifter ID,Name,Gender,Actual Weight,Age,Primary Weight Class,Primary Age Class\n"
        for lifter in lifters:
            lifters_csv += f"{lifter.lifter_id_number},{lifter.name},{lifter.gender},{lifter.actual_weight},{calculate_age(lifter.birth_date)},{lifter.primary_weight_class.name if lifter.primary_weight_class else 'N/A'},{lifter.primary_age_class.name if lifter.primary_age_class else 'N/A'}\n"

        lifts_csv = "Lift ID,Lifter Name,Lift Type,Attempt,Weight,Judge1,Judge2,Judge3,Overall Result\n"
        for lift in lifts:
            lifts_csv += f"{lift.id},{lift.lifter.name},{lift.lift_type},{lift.attempt_number},{lift.weight_lifted},{lift.judge1_score},{lift.judge2_score},{lift.judge3_score},{lift.overall_result}\n"

        print("\n--- LIFTERS EXPORT ---\n", lifters_csv)
        print("\n--- LIFTS EXPORT ---\n", lifts_csv)

        return jsonify({"message": "Data export simulated successfully. Check backend logs."}), 200
    except Exception as e:
        print(f"Error during export: {e}")
        return jsonify({"error": "Failed to export data", "details": str(e)}), 500

# Judge Login Route
@app.route('/login_judge', methods=['POST'])
def login_judge():
    data = request.get_json()
    pin = data.get('pin')
    if pin in JUDGE_PINS:
        return jsonify({"message": "Login successful", "judge_id": JUDGE_PINS[pin]}), 200
    else:
        return jsonify({"error": "Invalid PIN"}), 401

# Socket.IO Event Handlers
@socketio.on('connect')
def test_connect():
    print('Client connected')
    emit('after connect', {'data': 'Lets go!'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

# Initial database setup function - This MUST retain app_context as it runs outside a request
def create_tables():
    with app.app_context():
        # db.drop_all() # Keep this commented out after manual DROP SCHEMA public CASCADE
        db.create_all()
        
        # Populate initial data only if tables were just created (or dropped and recreated)
        if not MeetState.query.first():
            db.session.add(MeetState(current_lift_type='squat', current_attempt_number=1))
            db.session.commit()
        if not WeightClass.query.first():
            db.session.add_all([
                WeightClass(name="Men's 59kg", min_weight=0, max_weight=59, gender="Male"),
                WeightClass(name="Men's 66kg", min_weight=59.01, max_weight=66, gender="Male"),
                WeightClass(name="Men's 74kg", min_weight=66.01, max_weight=74, gender="Male"),
                WeightClass(name="Men's 83kg", min_weight=74.01, max_weight=83, gender="Male"),
                WeightClass(name="Men's 93kg", min_weight=83.01, max_weight=93, gender="Male"),
                WeightClass(name="Men's 105kg", min_weight=93.01, max_weight=105, gender="Male"),
                WeightClass(name="Men's 120kg", min_weight=105.01, max_weight=120, gender="Male"),
                WeightClass(name="Men's 120+kg", min_weight=120.01, max_weight=None, gender="Male"),
                WeightClass(name="Women's 47kg", min_weight=0, max_weight=47, gender="Female"),
                WeightClass(name="Women's 52kg", min_weight=47.01, max_weight=52, gender="Female"),
                WeightClass(name="Women's 57kg", min_weight=52.01, max_weight=57, gender="Female"),
                WeightClass(name="Women's 63kg", min_weight=57.01, max_weight=63, gender="Female"),
                WeightClass(name="Women's 69kg", min_weight=63.01, max_weight=69, gender="Female"),
                WeightClass(name="Women's 76kg", min_weight=69.01, max_weight=76, gender="Female"),
                WeightClass(name="Women's 84kg", min_weight=76.01, max_weight=84, gender="Female"),
                WeightClass(name="Women's 84+kg", min_weight=84.01, max_weight=None, gender="Female")
            ])
            db.session.commit()
        if not AgeClass.query.first():
            db.session.add_all([
                AgeClass(name="Sub-Junior", min_age=14, max_age=18),
                AgeClass(name="Junior", min_age=19, max_age=23),
                AgeClass(name="Open", min_age=24, max_age=39),
                AgeClass(name="Master I", min_age=40, max_age=49),
                AgeClass(name="Master II", min_age=50, max_age=59),
                AgeClass(name="Master III", min_age=60, max_age=69),
                AgeClass(name="Master IV", min_age=70, max_age=None)
            ])
            db.session.commit()

# Call create_tables() unconditionally to ensure database schema is initialized
create_tables()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
