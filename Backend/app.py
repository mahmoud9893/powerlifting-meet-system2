import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
# Add other necessary imports here, e.g., for pandas or openpyxl functions
import pandas as pd
# Assuming you have an initial data setup file or logic if needed, e.g., to load from Excel

app = Flask(__name__)
CORS(app) # Enable CORS for your Flask app

# --- Database Configuration ---
# The DATABASE_URL will be provided by Google Cloud Run as an environment variable.
# If running locally without this env var set, it will fall back to SQLite for development.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///powerlifting_meet.db' # Fallback for local development if DATABASE_URL is not set
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
# Configure SocketIO to use 'eventlet' and allow all origins for testing.
# For production, replace '*' with your specific frontend domain(s).
# message_queue=None is important for Cloud Run's stateless nature without a separate Redis/RabbitMQ.
socketio = SocketIO(app, cors_allowed_origins="*", message_queue=None, async_mode='eventlet')


# --- Define your SQLAlchemy Models (Lifter, LiftAttempt, WeightClass, AgeClass, MeetState) ---
# Example:
class WeightClass(db.Model):
    __tablename__ = 'weight_classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    min_weight = db.Column(db.Float, nullable=True)
    max_weight = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'min_weight': self.min_weight,
            'max_weight': self.max_weight
        }

class AgeClass(db.Model):
    __tablename__ = 'age_classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    min_age = db.Column(db.Integer, nullable=True)
    max_age = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'min_age': self.min_age,
            'max_age': self.max_age
        }

class Lifter(db.Model):
    __tablename__ = 'lifters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(10), nullable=False) # 'Male', 'Female'
    age = db.Column(db.Integer, nullable=False)
    bodyweight = db.Column(db.Float, nullable=False)
    weight_class_id = db.Column(db.Integer, db.ForeignKey('weight_classes.id'), nullable=True)
    age_class_id = db.Column(db.Integer, db.ForeignKey('age_classes.id'), nullable=True)
    entry_status = db.Column(db.String(50), default='Registered') # Registered, Active, Finished

    weight_class = db.relationship('WeightClass', backref='lifters')
    age_class = db.relationship('AgeClass', backref='lifters')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'bodyweight': self.bodyweight,
            'weight_class_id': self.weight_class_id,
            'weight_class_name': self.weight_class.name if self.weight_class else None,
            'age_class_id': self.age_class_id,
            'age_class_name': self.age_class.name if self.age_class else None,
            'entry_status': self.entry_status
        }

class LiftAttempt(db.Model):
    __tablename__ = 'lift_attempts'
    id = db.Column(db.Integer, primary_key=True)
    lifter_id = db.Column(db.Integer, db.ForeignKey('lifters.id'), nullable=False)
    lift_type = db.Column(db.String(50), nullable=False) # 'Squat', 'Bench', 'Deadlift'
    attempt_number = db.Column(db.Integer, nullable=False) # 1, 2, 3
    weight = db.Column(db.Float, nullable=False)
    score_status = db.Column(db.String(50), default='Pending') # 'Pending', 'Success', 'Fail'
    judge_scores = db.Column(db.JSON, default=lambda: [False, False, False]) # [J1_pass, J2_pass, J3_pass]
    time_stamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    lifter = db.relationship('Lifter', backref='lift_attempts')

    def to_dict(self):
        return {
            'id': self.id,
            'lifter_id': self.lifter_id,
            'lifter_name': self.lifter.name if self.lifter else None,
            'lift_type': self.lift_type,
            'attempt_number': self.attempt_number,
            'weight': self.weight,
            'score_status': self.score_status,
            'judge_scores': self.judge_scores,
            'time_stamp': self.time_stamp.isoformat() if self.time_stamp else None
        }

class MeetState(db.Model):
    __tablename__ = 'meet_state'
    id = db.Column(db.Integer, primary_key=True)
    current_lifter_id = db.Column(db.Integer, db.ForeignKey('lifters.id'), nullable=True)
    current_lift_type = db.Column(db.String(50), nullable=True)
    current_attempt_number = db.Column(db.Integer, nullable=True)
    is_meet_active = db.Column(db.Boolean, default=False)

    current_lifter = db.relationship('Lifter', foreign_keys=[current_lifter_id])

    def to_dict(self):
        return {
            'id': self.id,
            'current_lifter_id': self.current_lifter_id,
            'current_lifter_name': self.current_lifter.name if self.current_lifter else None,
            'current_lift_type': self.current_lift_type,
            'current_attempt_number': self.current_attempt_number,
            'is_meet_active': self.is_meet_active
        }

# --- Database Initialization (only runs if tables don't exist) ---
@app.before_first_request
def create_tables_and_seed_data():
    with app.app_context():
        # Check if tables exist. This is a simple check.
        # For production, consider Flask-Migrate for robust migrations.
        inspector = db.inspect(db.engine)
        if not inspector.has_table("lifters") or \
           not inspector.has_table("weight_classes") or \
           not inspector.has_table("age_classes") or \
           not inspector.has_table("lift_attempts") or \
           not inspector.has_table("meet_state"):
            db.create_all()
            print("Database tables created.")

            # Seed initial meet state
            if not MeetState.query.first():
                initial_state = MeetState(is_meet_active=False)
                db.session.add(initial_state)
                db.session.commit()
                print("Initial MeetState created.")
            
            # Seed initial weight and age classes (example data)
            if not WeightClass.query.first():
                weight_classes_data = [
                    {'name': 'Men\'s 59kg', 'min_weight': 53.01, 'max_weight': 59.0},
                    {'name': 'Men\'s 66kg', 'min_weight': 59.01, 'max_weight': 66.0},
                    {'name': 'Men\'s 74kg', 'min_weight': 66.01, 'max_weight': 74.0},
                    {'name': 'Men\'s 83kg', 'min_weight': 74.01, 'max_weight': 83.0},
                    {'name': 'Men\'s 93kg', 'min_weight': 83.01, 'max_weight': 93.0},
                    {'name': 'Men\'s 105kg', 'min_weight': 93.01, 'max_weight': 105.0},
                    {'name': 'Men\'s 120kg', 'min_weight': 105.01, 'max_weight': 120.0},
                    {'name': 'Men\'s 120+kg', 'min_weight': 120.01, 'max_weight': None},
                    {'name': 'Women\'s 47kg', 'min_weight': None, 'max_weight': 47.0},
                    {'name': 'Women\'s 52kg', 'min_weight': 47.01, 'max_weight': 52.0},
                    {'name': 'Women\'s 57kg', 'min_weight': 52.01, 'max_weight': 57.0},
                    {'name': 'Women\'s 63kg', 'min_weight': 57.01, 'max_weight': 63.0},
                    {'name': 'Women\'s 69kg', 'min_weight': 63.01, 'max_weight': 69.0},
                    {'name': 'Women\'s 76kg', 'min_weight': 69.01, 'max_weight': 76.0},
                    {'name': 'Women\'s 84kg', 'min_weight': 76.01, 'max_weight': 84.0},
                    {'name': 'Women\'s 84+kg', 'min_weight': 84.01, 'max_weight': None}
                ]
                for wc_data in weight_classes_data:
                    db.session.add(WeightClass(**wc_data))
                db.session.commit()
                print("Weight classes seeded.")
            
            if not AgeClass.query.first():
                age_classes_data = [
                    {'name': 'Sub-Junior (14-18)', 'min_age': 14, 'max_age': 18},
                    {'name': 'Junior (19-23)', 'min_age': 19, 'max_age': 23},
                    {'name': 'Open (24-39)', 'min_age': 24, 'max_age': 39},
                    {'name': 'Masters I (40-49)', 'min_age': 40, 'max_age': 49},
                    {'name': 'Masters II (50-59)', 'min_age': 50, 'max_age': 59},
                    {'name': 'Masters III (60-69)', 'min_age': 60, 'max_age': 69},
                    {'name': 'Masters IV (70+)', 'min_age': 70, 'max_age': None}
                ]
                for ac_data in age_classes_data:
                    db.session.add(AgeClass(**ac_data))
                db.session.commit()
                print("Age classes seeded.")

        else:
            print("Database tables already exist.")


# --- API Routes ---

# Test Route
@app.route('/')
def hello_world():
    return jsonify({"message": "Powerlifting Backend is running!"})

# Lifter Management
@app.route('/lifters', methods=['POST'])
def add_lifter():
    data = request.json
    name = data.get('name')
    gender = data.get('gender')
    age = data.get('age')
    bodyweight = data.get('bodyweight')

    if not all([name, gender, age, bodyweight]):
        return jsonify({"error": "Missing lifter data"}), 400

    # Determine weight class based on gender and bodyweight
    weight_class = None
    weight_classes_query = WeightClass.query.filter(WeightClass.name.like(f"{gender[0]}%")) # Assuming gender starts with M/W
    
    if gender == 'Male':
        weight_classes_query = WeightClass.query.filter(WeightClass.name.like('Men%'))
    elif gender == 'Female':
        weight_classes_query = WeightClass.query.filter(WeightClass.name.like('Women%'))
    
    weight_classes_for_gender = weight_classes_query.all()

    for wc in weight_classes_for_gender:
        if wc.min_weight is not None and wc.max_weight is not None:
            if wc.min_weight < bodyweight <= wc.max_weight:
                weight_class = wc
                break
        elif wc.min_weight is not None and wc.max_weight is None: # e.g., 120+kg
            if bodyweight > wc.min_weight:
                weight_class = wc
                break
        elif wc.min_weight is None and wc.max_weight is not None: # e.g., 47kg
            if bodyweight <= wc.max_weight:
                weight_class = wc
                break
    
    if not weight_class:
        return jsonify({"error": "Could not determine weight class for provided bodyweight and gender"}), 400

    # Determine age class based on age
    age_class = None
    age_classes = AgeClass.query.all()
    for ac in age_classes:
        if ac.min_age is not None and ac.max_age is not None:
            if ac.min_age <= age <= ac.max_age:
                age_class = ac
                break
        elif ac.min_age is not None and ac.max_age is None: # e.g., 70+
            if age >= ac.min_age:
                age_class = ac
                break
    
    if not age_class:
        return jsonify({"error": "Could not determine age class for provided age"}), 400

    try:
        new_lifter = Lifter(
            name=name,
            gender=gender,
            age=age,
            bodyweight=bodyweight,
            weight_class_id=weight_class.id,
            age_class_id=age_class.id
        )
        db.session.add(new_lifter)
        db.session.commit()
        return jsonify(new_lifter.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Lifter with this name already exists or database error"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route('/lifters', methods=['GET'])
def get_lifters():
    lifters = Lifter.query.all()
    return jsonify([lifter.to_dict() for lifter in lifters])

@app.route('/lifters/<int:lifter_id>', methods=['GET'])
def get_lifter(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if lifter:
        return jsonify(lifter.to_dict())
    return jsonify({"error": "Lifter not found"}), 404

@app.route('/lifters/<int:lifter_id>', methods=['PUT'])
def update_lifter(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"error": "Lifter not found"}), 404
    
    data = request.json
    lifter.name = data.get('name', lifter.name)
    lifter.gender = data.get('gender', lifter.gender)
    lifter.age = data.get('age', lifter.age)
    lifter.bodyweight = data.get('bodyweight', lifter.bodyweight)
    lifter.entry_status = data.get('entry_status', lifter.entry_status)

    # Re-determine weight class if bodyweight or gender changes
    if 'bodyweight' in data or 'gender' in data:
        weight_class = None
        current_gender = data.get('gender', lifter.gender)
        current_bodyweight = data.get('bodyweight', lifter.bodyweight)

        weight_classes_query = WeightClass.query.filter(WeightClass.name.like(f"{current_gender[0]}%"))
        if current_gender == 'Male':
            weight_classes_query = WeightClass.query.filter(WeightClass.name.like('Men%'))
        elif current_gender == 'Female':
            weight_classes_query = WeightClass.query.filter(WeightClass.name.like('Women%'))
        
        weight_classes_for_gender = weight_classes_query.all()

        for wc in weight_classes_for_gender:
            if wc.min_weight is not None and wc.max_weight is not None:
                if wc.min_weight < current_bodyweight <= wc.max_weight:
                    weight_class = wc
                    break
            elif wc.min_weight is not None and wc.max_weight is None:
                if current_bodyweight > wc.min_weight:
                    weight_class = wc
                    break
            elif wc.min_weight is None and wc.max_weight is not None:
                if current_bodyweight <= wc.max_weight:
                    weight_class = wc
                    break

        if weight_class:
            lifter.weight_class_id = weight_class.id
        else:
            return jsonify({"error": "Could not determine weight class for updated bodyweight and gender"}), 400

    # Re-determine age class if age changes
    if 'age' in data:
        age_class = None
        current_age = data.get('age', lifter.age)
        age_classes = AgeClass.query.all()
        for ac in age_classes:
            if ac.min_age is not None and ac.max_age is not None:
                if ac.min_age <= current_age <= ac.max_age:
                    age_class = ac
                    break
            elif ac.min_age is not None and ac.max_age is None:
                if current_age >= ac.min_age:
                    age_class = ac
                    break
        if age_class:
            lifter.age_class_id = age_class.id
        else:
            return jsonify({"error": "Could not determine age class for updated age"}), 400

    try:
        db.session.commit()
        return jsonify(lifter.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/lifters/<int:lifter_id>', methods=['DELETE'])
def delete_lifter(lifter_id):
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"error": "Lifter not found"}), 404
    try:
        db.session.delete(lifter)
        db.session.commit()
        return jsonify({"message": "Lifter deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Lift Attempt Management
@app.route('/lift_attempts', methods=['POST'])
def add_lift_attempt():
    data = request.json
    lifter_id = data.get('lifter_id')
    lift_type = data.get('lift_type')
    attempt_number = data.get('attempt_number')
    weight = data.get('weight')

    if not all([lifter_id, lift_type, attempt_number, weight]):
        return jsonify({"error": "Missing lift attempt data"}), 400
    
    lifter = Lifter.query.get(lifter_id)
    if not lifter:
        return jsonify({"error": "Lifter not found"}), 404

    try:
        new_attempt = LiftAttempt(
            lifter_id=lifter_id,
            lift_type=lift_type,
            attempt_number=attempt_number,
            weight=weight
        )
        db.session.add(new_attempt)
        db.session.commit()
        socketio.emit('new_lift_attempt', new_attempt.to_dict()) # Notify frontends
        return jsonify(new_attempt.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/lift_attempts', methods=['GET'])
def get_lift_attempts():
    attempts = LiftAttempt.query.all()
    return jsonify([attempt.to_dict() for attempt in attempts])

@app.route('/lift_attempts/<int:attempt_id>', methods=['PUT'])
def update_lift_attempt(attempt_id):
    attempt = LiftAttempt.query.get(attempt_id)
    if not attempt:
        return jsonify({"error": "Lift attempt not found"}), 404
    
    data = request.json
    attempt.score_status = data.get('score_status', attempt.score_status)
    attempt.judge_scores = data.get('judge_scores', attempt.judge_scores)

    try:
        db.session.commit()
        socketio.emit('lift_attempt_updated', attempt.to_dict()) # Notify frontends
        return jsonify(attempt.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Meet State Management
@app.route('/meet_state', methods=['GET'])
def get_meet_state():
    state = MeetState.query.first()
    if state:
        return jsonify(state.to_dict())
    return jsonify({"error": "Meet state not found"}), 404 # Should ideally always exist after create_tables

@app.route('/meet_state', methods=['PUT'])
def update_meet_state():
    state = MeetState.query.first()
    if not state:
        return jsonify({"error": "Meet state not found. Please initialize."}), 404

    data = request.json
    state.current_lifter_id = data.get('current_lifter_id', state.current_lifter_id)
    state.current_lift_type = data.get('current_lift_type', state.current_lift_type)
    state.current_attempt_number = data.get('current_attempt_number', state.current_attempt_number)
    state.is_meet_active = data.get('is_meet_active', state.is_meet_active)

    try:
        db.session.commit()
        socketio.emit('meet_state_updated', state.to_dict()) # Notify frontends
        return jsonify(state.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Import Data from Excel (Organizer function)
@app.route('/import_excel', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        try:
            df = pd.read_excel(file)
            
            # Assuming columns: Name, Gender, Age, Bodyweight
            # Map these to your Lifter model and add to DB
            for index, row in df.iterrows():
                name = row['Name']
                gender = row['Gender']
                age = int(row['Age'])
                bodyweight = float(row['Bodyweight'])

                # Logic to determine weight_class_id and age_class_id (from add_lifter route)
                weight_class = None
                weight_classes_query = WeightClass.query.filter(WeightClass.name.like(f"{gender[0]}%"))
                if gender == 'Male':
                    weight_classes_query = WeightClass.query.filter(WeightClass.name.like('Men%'))
                elif gender == 'Female':
                    weight_classes_query = WeightClass.query.filter(WeightClass.name.like('Women%'))
                
                weight_classes_for_gender = weight_classes_query.all()

                for wc in weight_classes_for_gender:
                    if wc.min_weight is not None and wc.max_weight is not None:
                        if wc.min_weight < bodyweight <= wc.max_weight:
                            weight_class = wc
                            break
                    elif wc.min_weight is not None and wc.max_weight is None:
                        if bodyweight > wc.min_weight:
                            weight_class = wc
                            break
                    elif wc.min_weight is None and wc.max_weight is not None:
                        if bodyweight <= wc.max_weight:
                            weight_class = wc
                            break
                
                if not weight_class:
                    print(f"Warning: Could not determine weight class for {name}, skipping.")
                    continue # Skip this row

                age_class = None
                age_classes = AgeClass.query.all()
                for ac in age_classes:
                    if ac.min_age is not None and ac.max_age is not None:
                        if ac.min_age <= age <= ac.max_age:
                            age_class = ac
                            break
                    elif ac.min_age is not None and ac.max_age is None:
                        if age >= ac.min_age:
                            age_class = ac
                            break
                
                if not age_class:
                    print(f"Warning: Could not determine age class for {name}, skipping.")
                    continue # Skip this row

                try:
                    new_lifter = Lifter(
                        name=name,
                        gender=gender,
                        age=age,
                        bodyweight=bodyweight,
                        weight_class_id=weight_class.id,
                        age_class_id=age_class.id
                    )
                    db.session.add(new_lifter)
                    db.session.commit() # Commit each lifter or batch commit for performance
                except IntegrityError:
                    db.session.rollback()
                    print(f"Lifter {name} already exists or database error, skipping.")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error adding lifter {name}: {str(e)}, skipping.")

            return jsonify({"message": "Lifters imported successfully"}), 200
        except Exception as e:
            return jsonify({"error": f"Failed to process Excel file: {str(e)}"}), 500

# Judge Login Endpoint
@app.route('/judge_login', methods=['POST'])
def judge_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Simple hardcoded check for demonstration purposes
    # In a real app, integrate with a proper auth system (e.g., Firebase Auth, Auth0)
    if username == 'judge' and password == 'password123':
        # Return a simple token or session info for the judge (e.g., just a success message for this demo)
        return jsonify({"message": "Judge login successful", "token": "dummy_judge_token"}), 200
    else:
        return jsonify({"error": "Invalid judge credentials"}), 401

# Current Lift Information for Public Display and Judge App
@app.route('/current_lift', methods=['GET'])
def get_current_lift_info():
    meet_state = MeetState.query.first()
    if not meet_state or not meet_state.is_meet_active:
        return jsonify({"current_lift": None, "message": "Meet is not active or no lift in progress"}), 200

    current_lifter = meet_state.current_lifter
    if not current_lifter:
        return jsonify({"current_lift": None, "message": "No lifter currently set"}), 200
    
    # Fetch previous attempts for the current lifter and lift type
    previous_attempts = LiftAttempt.query.filter_by(
        lifter_id=current_lifter.id,
        lift_type=meet_state.current_lift_type
    ).order_by(LiftAttempt.attempt_number.asc()).all()

    current_lift_info = {
        "lifter_name": current_lifter.name,
        "gender": current_lifter.gender,
        "age": current_lifter.age,
        "bodyweight": current_lifter.bodyweight,
        "weight_class": current_lifter.weight_class.name if current_lifter.weight_class else "N/A",
        "age_class": current_lifter.age_class.name if current_lifter.age_class else "N/A",
        "lift_type": meet_state.current_lift_type,
        "attempt_number": meet_state.current_attempt_number,
        "previous_attempts": [att.to_dict() for att in previous_attempts]
    }
    return jsonify({"current_lift": current_lift_info}), 200


# SocketIO Events (Example)
@socketio.on('connect')
def connect():
    print(f'Client connected: {request.sid}')
    # Emit current meet state to newly connected client
    with app.app_context():
        state = MeetState.query.first()
        if state:
            emit('meet_state_updated', state.to_dict())
        else:
            print("No meet state found to emit on connect.")

@socketio.on('disconnect')
def disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('update_meet_state_from_organizer')
def update_meet_state_socket(data):
    # This event would be triggered by the Organizer app
    with app.app_context():
        state = MeetState.query.first()
        if not state:
            print("Meet state not found for update from organizer.")
            return

        state.current_lifter_id = data.get('current_lifter_id', state.current_lifter_id)
        state.current_lift_type = data.get('current_lift_type', state.current_lift_type)
        state.current_attempt_number = data.get('current_attempt_number', state.current_attempt_number)
        state.is_meet_active = data.get('is_meet_active', state.is_meet_active)

        db.session.commit()
        # Emit the updated state to all connected clients (Public Display, Judge, other Organizers)
        socketio.emit('meet_state_updated', state.to_dict())
        print(f"Meet state updated by organizer: {state.to_dict()}")

@socketio.on('submit_score')
def handle_submit_score(data):
    # This event would be triggered by the Judge app
    attempt_id = data.get('attempt_id')
    judge_index = data.get('judge_index') # 0, 1, or 2
    passed = data.get('passed') # True or False

    with app.app_context():
        attempt = LiftAttempt.query.get(attempt_id)
        if not attempt:
            print(f"Lift attempt {attempt_id} not found for scoring.")
            return

        scores = list(attempt.judge_scores) # Convert JSON list to mutable Python list
        scores[judge_index] = passed
        attempt.judge_scores = scores # Assign back to JSON field

        # Determine overall score status (2 out of 3 judges must pass)
        pass_count = sum(1 for s in scores if s is True)
        if pass_count >= 2:
            attempt.score_status = 'Success'
        elif False in scores and True not in scores and None not in scores: # All judges failed and no None scores
            attempt.score_status = 'Fail'
        elif all(s is not None for s in scores) and pass_count < 2: # All scores in, but less than 2 passes
            attempt.score_status = 'Fail'
        else:
            attempt.score_status = 'Pending' # Still waiting for more scores

        db.session.commit()
        # Emit the updated attempt to all connected clients
        socketio.emit('lift_attempt_updated', attempt.to_dict())
        print(f"Lift attempt {attempt_id} scored: {attempt.to_dict()}")

if __name__ == '__main__':
    # This block runs when the script is executed directly (e.g., during local development).
    # Gunicorn will handle running the app in production on Cloud Run.
    # We use socketio.run instead of app.run for Flask-SocketIO.
    # host="0.0.0.0" is necessary to make the app accessible externally,
    # and the port is taken from the PORT env var for Cloud Run, or defaults to 5000 locally.
    socketio.run(app, debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
