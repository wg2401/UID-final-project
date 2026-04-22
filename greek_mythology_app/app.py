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

def load_learn_routes():
    with open("data/learn.json") as f:
        return json.load(f)

def load_lessons():
    with open("data/lessons.json") as f:
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

def get_learning_progress():
    return session.get("learning_progress", {
        "started_at": None,
        "visited_topics": [],
        "completed_topics": [],
        "checkpoint_answers": {},
        "checkpoint_completed_at": None
    })

#Home
@app.route("/")
def index():
    return render_template("index.html")


# Start learning
@app.route("/start/learn")
def start_learn():
    session["learning_progress"] = {
        "started_at": str(datetime.datetime.now()),
        "visited_topics": [],
        "completed_topics": [],
        "checkpoint_answers": {},
        "checkpoint_completed_at": None
    }
    return redirect(url_for("learn_index"))


# Learning index
@app.route("/learn")
def learn_index():
    lessons_data = load_lessons()
    lessons = lessons_data["lessons"]

    progress = get_learning_progress()
    lesson_order = ["zeus", "poseidon", "athena", "aphrodite", "relationships", "symbols"]

    completed_count = len([topic for topic in progress["completed_topics"] if topic in lesson_order])
    total_topics = len(lesson_order)

    return render_template(
        "learn/index.html",
        lessons=lessons,
        completed_count=completed_count,
        total_topics=total_topics
    )


@app.route("/learn/<topic>")
def learn(topic):
    progress = get_learning_progress()

    progress["visited_topics"].append({
        "topic": topic,
        "entered_at": str(datetime.datetime.now())
    })

    session["learning_progress"] = progress

    return render_template(f"learn/{topic}.html", topic=topic)


@app.route("/learn/complete/<topic>", methods=["POST"])
def complete_topic(topic):
    progress = get_learning_progress()
    lesson_order = ["zeus", "poseidon", "athena", "aphrodite", "relationships", "symbols"]

    if topic not in progress["completed_topics"]:
        progress["completed_topics"].append(topic)

    session["learning_progress"] = progress

    if topic in lesson_order:
        current_index = lesson_order.index(topic)
        if current_index < len(lesson_order) - 1:
            next_topic = lesson_order[current_index + 1]
            return redirect(url_for("learn", topic=next_topic))

    return redirect(url_for("learn_index"))


@app.route("/learn/checkpoint/save", methods=["POST"])
def save_checkpoint():
    progress = get_learning_progress()

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    progress["checkpoint_answers"] = data
    progress["checkpoint_completed_at"] = str(datetime.datetime.now())
    session["learning_progress"] = progress

    return jsonify({"status": "ok"})


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



@app.route('/data/<path:filename>')
def data_files(filename):
    return send_from_directory('data', filename)


if __name__ == "__main__":
    app.run(debug=True)