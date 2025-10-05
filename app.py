from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
import json
import re

app = Flask(__name__)
CORS(app) # Enable CORS for all routes, so frontend can communicate

# --- Configure Google Generative AI ---
# WARNING: Directly embedding your API key in code is NOT recommended for deployment.
# It is used here for simplified local testing. For production, ALWAYS use environment variables.
GOOGLE_API_KEY = "AIzaSyAbDRav7Kj6yRVBEJMFaUPz0SbKDe6weoM" # Your provided API key
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-pro-latest') # Or 'gemini-1.5-flash-latest' for newer models

# --- Helper function to parse AI's text response into structured JSON ---
def parse_quiz_response(text_response):
    questions = []
    # Regex to find blocks of questions. Added a stricter start for block to handle intro text.
    # Also added re.IGNORECASE for "Question" and re.MULTILINE to catch start of line.
    question_blocks = re.findall(r'(^##\s*Question\s*\d+:\s*.*?)(?=\n^##\s*Question|\Z)', text_response, re.DOTALL | re.MULTILINE | re.IGNORECASE)

    if not question_blocks:
        print("No question blocks found with initial regex, trying alternative...")
        # Fallback regex if the AI's formatting varies slightly
        question_blocks = re.findall(r'(Question\s*\d+:.*?)(?=(?:Question\s*\d+:)|$)', text_response, re.DOTALL | re.IGNORECASE)


    for block in question_blocks:
        # Clean up block by removing leading/trailing whitespace and potentially initial "## Question X:"
        block_clean = block.strip()
        block_clean = re.sub(r'^##\s*Question\s*\d+:\s*', '', block_clean, flags=re.IGNORECASE)

        question_match = re.search(r'^(.*?)(?=\n\s*Options:)', block_clean, re.DOTALL | re.IGNORECASE)
        options_match = re.search(r'Options:\n(.*?)(?=\n\s*Correct Answer:)', block_clean, re.DOTALL | re.IGNORECASE)
        correct_answer_match = re.search(r'Correct Answer:\s*(.*?)(?=\n\s*Solution:|\Z)', block_clean, re.DOTALL | re.IGNORECASE)
        solution_match = re.search(r'Solution:\s*(.*)', block_clean, re.DOTALL | re.IGNORECASE)

        if question_match and options_match and correct_answer_match and solution_match:
            question_text = question_match.group(1).strip()
            options_text = options_match.group(1).strip()
            correct_answer = correct_answer_match.group(1).strip()
            solution = solution_match.group(1).strip()

            options_list = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
            # Clean up options (e.g., remove A. B. C. D.)
            options_cleaned = []
            for opt in options_list:
                cleaned_opt = re.sub(r'^[A-D]\.\s*', '', opt, flags=re.IGNORECASE).strip()
                if cleaned_opt: # Ensure we don't add empty strings
                    options_cleaned.append(cleaned_opt)

            # Clean correct answer by removing any leading A. B. C. D.
            cleaned_correct_answer = re.sub(r'^[A-D]\.\s*', '', correct_answer, flags=re.IGNORECASE).strip()

            # Ensure 'id' is unique for each question
            questions.append({
                "id": len(questions) + 1,
                "question": question_text,
                "options": options_cleaned,
                "correctAnswer": cleaned_correct_answer,
                "solution": solution
            })
        else:
            print(f"Failed to parse a question block. Missing components in: \n---Block---\n{block_clean}\n---End Block---")
    return questions

# --- API Endpoint to Generate Quiz Questions ---
@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    data = request.json
    subject = data.get('subject')
    chapter = data.get('chapter')
    limit = data.get('limit', 10) # Default to 10 questions

    if not all([subject, chapter, limit]):
        return jsonify({"error": "Missing subject, chapter, or limit"}), 400

    prompt = f"""
    Generate {limit} multiple-choice questions for NEET students on the topic of "{chapter}" in "{subject}".
    Each question should have exactly 4 options (A, B, C, D).
    For each question, also provide the correct answer and a detailed explanation (solution).

    Format the output strictly as follows:

    ## Question 1: [Question text]
    Options:
    A. [Option A text]
    B. [Option B text]
    C. [Option C text]
    D. [Option D text]
    Correct Answer: [Exact text of the correct option, including potential leading identifier if present in options]
    Solution: [Detailed explanation for the correct answer and why other options are wrong]

    ## Question 2: [Question text]
    Options:
    A. [Option A text]
    B. [Option B text]
    C. [Option C text]
    D. [Option D text]
    Correct Answer: [Exact text of the correct option, including potential leading identifier if present in options]
    Solution: [Detailed explanation]

    ... and so on for {limit} questions.
    Ensure the "Correct Answer" exactly matches one of the "Options" provided for that question.
    """

    try:
        response = model.generate_content(prompt)
        generated_text = response.text
        print("Raw AI Response:\n", generated_text) # For debugging purposes

        questions = parse_quiz_response(generated_text)
        if not questions:
            print("Parsing resulted in zero questions. Attempting to return raw text as a single question if parsing completely failed.")
            return jsonify({"error": "AI generated no parsable questions. Please try again. Raw response might be in console.", "raw_response": generated_text}), 500

        # Post-processing to ensure correct answer matches an option if AI includes A. B. etc.
        # This is a common AI parsing challenge.
        for q in questions:
            cleaned_correct_answer = re.sub(r'^[A-D]\.\s*', '', q['correctAnswer'], flags=re.IGNORECASE).strip()
            # Try to find a match in the options
            matched_option = None
            for opt in q['options']:
                if opt.strip() == cleaned_correct_answer:
                    matched_option = opt
                    break
            if matched_option:
                q['correctAnswer'] = matched_option
            else:
                # Fallback: if AI's 'Correct Answer' is just 'C', and option C is 'Photosynthesis', try to find 'Photosynthesis'
                # This is a complex problem to perfectly solve with regex. Better AI prompting helps.
                pass


        return jsonify({"questions": questions})
    except Exception as e:
        print(f"Error generating content: {e}")
        return jsonify({"error": f"Failed to generate quiz from AI: {str(e)}"}), 500

# --- Optional: API Endpoint for AI-powered result analysis ---
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

    analysis_prompt = f"""
    A NEET student just completed a quiz. They answered {correct_count} out of {len(quiz)} questions correctly.

    Here are the details of the questions they answered incorrectly, along with the correct answers and solutions:
    {json.dumps(wrong_questions_details, indent=2)}

    Based on this information, provide:
    1. An overall feedback message to the student about their performance (e.g., "Good effort, keep practicing!", "You have a strong foundation but need to revise X").
    2. Suggest 2-3 specific sub-topics or concepts they should focus on for improvement, directly related to their wrong answers.
    3. Encourage them and suggest practical ways to practice effectively (e.g., "Review concepts in your textbook," "Try solving similar problems").
    """

    try:
        response = model.generate_content(analysis_prompt)
        overall_feedback = response.text.strip()
        return jsonify({"overallFeedback": overall_feedback, "score": correct_count})
    except Exception as e:
        print(f"Error analyzing results with AI: {e}")
        return jsonify({"error": f"Failed to get AI analysis: {str(e)}", "score": correct_count}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)