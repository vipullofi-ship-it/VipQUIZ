from flask import Flask, request, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- Helper function to generate mock questions ---
def generate_mock_questions(subject, chapter, limit=10):
    questions = []
    for i in range(1, limit + 1):
        options = ["Option A", "Option B", "Option C", "Option D"]
        correct_answer = random.choice(options)
        questions.append({
            "id": i,
            "question": f"Sample question {i} for {subject}-{chapter}?",
            "options": options,
            "correctAnswer": correct_answer,
            "solution": f"This is a mock solution for question {i}."
        })
    return questions

# --- API Endpoint to Generate Quiz Questions ---
@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    data = request.json
    subject = data.get('subject')
    chapter = data.get('chapter')
    limit = data.get('limit', 10)

    if not all([subject, chapter, limit]):
        return jsonify({"error": "Missing subject, chapter, or limit"}), 400

    questions = generate_mock_questions(subject, chapter, limit)
    return jsonify({"questions": questions})

# --- API Endpoint for Mock Result Analysis ---
@app.route('/analyze_results', methods=['POST'])
def analyze_results():
    data = request.json
    quiz = data.get('quiz', [])
    user_answers = data.get('userAnswers', [])

    if not quiz or not user_answers:
        return jsonify({"error": "Missing quiz or user answers data for analysis"}), 400

    correct_count = 0
    wrong_questions_details = []

    for user_ans in user_answers:
        question_obj = next((q for q in quiz if q['id'] == user_ans['questionId']), None)
        if question_obj:
            if user_ans['selectedAnswer'] == question_obj['correctAnswer']:
                correct_count += 1
            else:
                wrong_questions_details.append({
                    "question": question_obj['question'],
                    "your_answer": user_ans['selectedAnswer'],
                    "correct_answer": question_obj['correctAnswer'],
                    "provided_solution": question_obj['solution']
                })

    # Free mock analysis
    overall_feedback = f"You answered {correct_count} out of {len(quiz)} questions correctly. " \
                       f"Review the topics of your wrong answers: " + \
                       ", ".join([w['question'] for w in wrong_questions_details[:3]]) + ". " \
                       f"Keep practicing to improve your score!"

    return jsonify({"overallFeedback": overall_feedback, "score": correct_count})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)
