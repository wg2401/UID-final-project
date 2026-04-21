#app.py
import json
import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = "mythology123"

def load_questions():
    with open("data/questions.json") as f:
        return json.load(f)

def normalize_text(s):
    s = s.strip().lower()
    s = s.replace(",", "")
    s = s.replace(".", "")
    s = s.replace("the ", "")
    return s

def text_answer_is_correct(user_answer, correct_answer):
    user_answer = normalize_text(user_answer)

    if isinstance(correct_answer, list):
        for answer in correct_answer:
            if user_answer == normalize_text(answer):
                return True
        return False

    return user_answer == normalize_text(correct_answer)

#Home
@app.route("/")
def index():
    return render_template("index.html")


#Quiz 1
@app.route("/start/quiz")
def start_quiz():
    session["quiz_answers"] = {}
    session["quiz_start_time"] = str(datetime.datetime.now())
    return redirect(url_for("quiz", question_num=1))

@app.route("/quiz/<int:question_num>", methods=["GET", "POST"])
def quiz(question_num):
    data = load_questions()
    questions = data["quiz"]

    if question_num < 1 or question_num > len(questions):
        return redirect(url_for("index"))

    if request.method == "POST":
        selected = request.form.get("choice")
        answers = session.get("quiz_answers", {})
        answers[str(question_num)] = selected
        session["quiz_answers"] = answers
        return redirect(url_for("feedback", quiz_type="quiz", question_num=question_num))

    question = questions[question_num - 1]
    return render_template("quiz.html", question=question, question_num=question_num,
                           total=len(questions), title="Quiz")


#Final Quiz
@app.route("/start/final")
def start_final():
    session["final_answers"] = {}
    session["final_start_time"] = str(datetime.datetime.now())
    return redirect(url_for("final_quiz", question_num=1))

@app.route("/final/<int:question_num>", methods=["GET", "POST"])
def final_quiz(question_num):
    data = load_questions()
    questions = data["final_quiz"]

    if question_num < 1 or question_num > len(questions):
        return redirect(url_for("index"))

    if request.method == "POST":
        selected = request.form.get("choice") or request.form.get("text_answer", "").strip()
        answers = session.get("final_answers", {})
        answers[str(question_num)] = selected
        session["final_answers"] = answers
        return redirect(url_for("feedback", quiz_type="final", question_num=question_num))

    question = questions[question_num - 1]
    return render_template("quiz.html", question=question, question_num=question_num,
                           total=len(questions), title="Final Quiz")


#Feedback
@app.route("/feedback/<quiz_type>/<int:question_num>")
def feedback(quiz_type, question_num):
    data = load_questions()
    key = "final_quiz" if quiz_type == "final" else "quiz"
    questions = data[key]
    question = questions[question_num - 1]

    if quiz_type == "quiz":
        answers = session.get("quiz_answers", {})
    else:
        answers = session.get("final_answers", {})

    user_answer = answers.get(str(question_num), "No answer")
    correct_answer = question["answer"]

    if question.get("type") == "text":
        correct = text_answer_is_correct(user_answer, correct_answer)
    else:
        correct = user_answer == correct_answer

    total = len(questions)

    if question_num < total:
        if quiz_type == "quiz":
            next_url = url_for("quiz", question_num=question_num + 1)
        else:
            next_url = url_for("final_quiz", question_num=question_num + 1)
    else:
        next_url = url_for("results", quiz_type=quiz_type)

    if isinstance(correct_answer, list):
        correct_answer_display = ", ".join(correct_answer)
    else:
        correct_answer_display = correct_answer

    return render_template("feedback.html", correct=correct, correct_answer=correct_answer_display,
                        user_answer=user_answer, next_url=next_url,
                        question_num=question_num, total=total)


#Results
@app.route("/results/<quiz_type>")
def results(quiz_type):
    data = load_questions()

    if quiz_type == "quiz":
        questions = data["quiz"]
        answers = session.get("quiz_answers", {})
        retry_url = url_for("start_quiz")
    else:
        questions = data["final_quiz"]
        answers = session.get("final_answers", {})
        retry_url = url_for("start_final")

    score = 0
    breakdown = []

    for i, q in enumerate(questions):
        user_answer = answers.get(str(i + 1), "No answer")
        correct_answer = q["answer"]

        if q.get("type") == "text":
            correct = text_answer_is_correct(user_answer, correct_answer)
        else:
            correct = user_answer == correct_answer

        if correct:
            score += 1

        breakdown.append({
            "question": q["question"],
            "user_answer": user_answer,
            "correct_answer": ", ".join(correct_answer) if isinstance(correct_answer, list) else correct_answer,
            "correct": correct
        })

    return render_template("results.html", score=score, total=len(questions),
                           breakdown=breakdown, retry_url=retry_url)


@app.route("/learn/<topic>")
def learn(topic):
    return render_template(f"learn/{topic}.html")

@app.route('/data/<path:filename>')
def data_files(filename):
    return send_from_directory('data', filename)


if __name__ == "__main__":
    app.run(debug=True)