from flask import Flask, render_template, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'TiG86I1lpk6TQWajLlTXwkWjNxbQBJA5'

#SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User table for storing user information
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    best_score = db.Column(db.Integer, default=0)
    submission_date = db.Column(db.String(50), nullable=False)

# Submission table for storing each quiz submission
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    submission_date = db.Column(db.String(50), nullable=False)

# Create database schema
with app.app_context():
    db.create_all()

# Correct answers for grading
correct_answers = {
    "question1": "Artificial Intelligence",
    "question2": "Recognizing objects in images",
    "question3": "8",
    "question4": "TensorFlow",
    "question5": "List"
}

@app.route('/')
def home():
    # Calculating the best score among all users
    best_score_overall = db.session.query(db.func.max(Submission.score)).scalar() or 0
    return render_template('quiz.html', best_score=best_score_overall)

@app.route('/submit', methods=['POST'])
def submit():
    username = request.form.get('username')
    score = 0

    # Grading the quiz
    for question, correct_answer in correct_answers.items():
        user_answer = request.form.get(question)
        if user_answer == correct_answer:
            score += 20  # Each question is worth 20%

    # Current date and time in DD/MM/YYYY HH:MM:SS format
    current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Retrieving or creating user in the database
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, best_score=score, submission_date=current_datetime)
        db.session.add(user)
    else:
        # Updating the user's best score if the new score is higher
        user.best_score = max(user.best_score, score)
        user.submission_date = current_datetime

    db.session.flush()

    # Saving the submission
    submission = Submission(user_id=user.id, score=score, submission_date=current_datetime)
    db.session.add(submission)
    db.session.commit()

    # Calculating the best score among all submissions to display on the top-right corner of the page
    best_score_overall = db.session.query(db.func.max(Submission.score)).scalar()

    # Return JSON response
    return jsonify({
        'username': username,
        'score': score,
        'best_score': best_score_overall,
        'submission_date': current_datetime
    })

@app.route('/user-scores', methods=['GET'])
def user_scores():
    # Query all users and their best scores
    users = User.query.with_entities(User.username, User.best_score).all()


    # Converting the query result to a list of dictionaries
    user_scores = [{"username": user.username, "best_score": user.best_score} for user in users]

    return jsonify(user_scores)


if __name__ == '__main__':
    app.run(debug=True)
