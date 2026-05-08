import json
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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

LESSON_ORDER = ["zeus", "poseidon", "athena", "aphrodite", "relationships", "symbols"]

CHECKPOINT_ANSWER_KEY = {
    "thunderbolt": "zeus",
    "trident": "poseidon",
    "owl": "athena",
    "dove": "aphrodite"
}

CHECKPOINT_MIN_SCORE = 3
FINAL_UNLOCK_MIN_SCORE = 10


def build_learning_progress():
    return {
        "started_at": None,
        "visited_topics": [],
        "completed_topics": [],
        "section_status": {},
        "checkpoint_answers": {},
        "checkpoint_completed_at": None,
        "checkpoint_score": 0,
        "checkpoint_total": len(CHECKPOINT_ANSWER_KEY),
        "checkpoint_passed": False,
        "quiz_scores": {
            "quiz": None,
            "final": None
        },
        "unlock_state": {
            "quiz_unlocked": False,
            "final_unlocked": False
        }
    }


def update_unlock_state(progress):
    completed_count = len([topic for topic in progress["completed_topics"] if topic in LESSON_ORDER])

    quiz_score = 0
    if progress["quiz_scores"]["quiz"] is not None:
        quiz_score = progress["quiz_scores"]["quiz"]["score"]

    progress["unlock_state"] = {
        "quiz_unlocked": completed_count == len(LESSON_ORDER) and progress["checkpoint_passed"],
        "final_unlocked": quiz_score >= FINAL_UNLOCK_MIN_SCORE
    }

    return progress

def get_learning_progress():
    progress = session.get("learning_progress")

    if not progress:
        progress = build_learning_progress()

    if "visited_topics" not in progress:
        progress["visited_topics"] = []

    if "completed_topics" not in progress:
        progress["completed_topics"] = []

    if "section_status" not in progress:
        progress["section_status"] = {}

    if "checkpoint_answers" not in progress:
        progress["checkpoint_answers"] = {}

    if "checkpoint_completed_at" not in progress:
        progress["checkpoint_completed_at"] = None

    if "checkpoint_score" not in progress:
        progress["checkpoint_score"] = 0

    if "checkpoint_total" not in progress:
        progress["checkpoint_total"] = len(CHECKPOINT_ANSWER_KEY)

    if "checkpoint_passed" not in progress:
        progress["checkpoint_passed"] = False

    if "quiz_scores" not in progress:
        progress["quiz_scores"] = {
            "quiz": None,
            "final": None
        }

    if "quiz" not in progress["quiz_scores"]:
        progress["quiz_scores"]["quiz"] = None

    if "final" not in progress["quiz_scores"]:
        progress["quiz_scores"]["final"] = None

    if "unlock_state" not in progress:
        progress["unlock_state"] = {
            "quiz_unlocked": False,
            "final_unlocked": False
        }

    progress = update_unlock_state(progress)
    return progress

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start/learn")
def start_learn():
    progress = get_learning_progress()
    if progress["started_at"] is None:
        progress["started_at"] = str(datetime.datetime.now())
    progress = update_unlock_state(progress)
    session["learning_progress"] = progress
    return redirect(url_for("learn_index"))


@app.route("/learn")
def learn_index():
    lessons_data = load_lessons()
    lessons = lessons_data["lessons"]

    progress = get_learning_progress()
    completed_count = len([topic for topic in progress["completed_topics"] if topic in LESSON_ORDER])
    total_topics = len(LESSON_ORDER)

    session["learning_progress"] = progress

    return render_template(
        "learn/index.html",
        lessons=lessons,
        progress=progress,
        completed_count=completed_count,
        total_topics=total_topics
    )

@app.route("/match")
def match():
    return render_template("match.html")

@app.route("/match/submit", methods=["POST"])
def match_submit():
    data = request.get_json()

    correct_map = {
        "1": "4",  
        "2": "2",  
        "3": "1",  
        "4": "3"   
    }

    LEFT_MAP = {
        "1": "Zeus",
        "2": "Poseidon",
        "3": "Athena",
        "4": "Aphrodite"
    }

    RIGHT_MAP = {
        "1": "Owl",
        "2": "Trident",
        "3": "Dove",
        "4": "Thunderbolt"
    }

    score = 0
    total = len(correct_map)
    results = []

    for left_id, right_id in data.items():
        is_correct = correct_map.get(left_id) == right_id
        if is_correct:
            score += 1
        results.append({
            "left":    LEFT_MAP.get(left_id, left_id),
            "right":   RIGHT_MAP.get(right_id, right_id),
            "correct": is_correct
        })

    progress = get_learning_progress()
    progress["checkpoint_score"]        = score
    progress["checkpoint_total"]        = total
    progress["checkpoint_passed"]       = score >= CHECKPOINT_MIN_SCORE
    progress["checkpoint_completed_at"] = str(datetime.datetime.now())
    progress = update_unlock_state(progress)
    session["learning_progress"] = progress

    passed = progress["checkpoint_passed"]
    quiz_unlocked = progress["unlock_state"]["quiz_unlocked"]

    return render_template(
        "match_results.html",
        score=score,
        total=total,
        results=results,
        passed=passed,
        quiz_unlocked=quiz_unlocked
    )

@app.route("/learn/<topic>")
def learn(topic):
    if topic not in LESSON_ORDER:
        return redirect(url_for("learn_index"))

    progress = get_learning_progress()
    now = str(datetime.datetime.now())

    if topic not in progress["section_status"]:
        progress["section_status"][topic] = {
            "visited": False,
            "completed": False,
            "first_entered_at": now,
            "last_entered_at": now,
            "completed_at": None,
            "visits": 1
        }
    else:
        progress["section_status"][topic]["last_entered_at"] = now
        progress["section_status"][topic]["visits"] = progress["section_status"][topic]["visits"] + 1

    progress["section_status"][topic]["visited"] = True

    progress["visited_topics"].append({
        "topic": topic,
        "entered_at": now
    })

    progress = update_unlock_state(progress)
    session["learning_progress"] = progress

    return render_template(f"learn/{topic}.html", topic=topic)


@app.route("/learn/complete/<topic>", methods=["POST"])
def complete_topic(topic):
    if topic not in LESSON_ORDER:
        return redirect(url_for("learn_index"))

    progress = get_learning_progress() 
    now = str(datetime.datetime.now())

    if topic not in progress["completed_topics"]:
        progress["completed_topics"].append(topic)

    if topic not in progress["section_status"]:
        progress["section_status"][topic] = {
            "visited": True,
            "completed": True,
            "first_entered_at": now,
            "last_entered_at": now,
            "completed_at": now,
            "visits": 1
        }
    else:
        progress["section_status"][topic]["visited"] = True
        progress["section_status"][topic]["completed"] = True
        progress["section_status"][topic]["completed_at"] = now
        progress["section_status"][topic]["last_entered_at"] = now

    progress = update_unlock_state(progress)
    session["learning_progress"] = progress

    current_index = LESSON_ORDER.index(topic)
    if current_index < len(LESSON_ORDER) - 1:
        next_topic = LESSON_ORDER[current_index + 1]
        return redirect(url_for("learn", topic=next_topic))

    return redirect(url_for("learn_index"))


@app.route("/learn/checkpoint/save", methods=["POST"])
def save_checkpoint():
    progress = get_learning_progress()

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    normalized_answers = {}
    for key, value in data.items():
        normalized_answers[str(key).strip().lower()] = str(value).strip().lower()

    score = 0
    for symbol, correct_god in CHECKPOINT_ANSWER_KEY.items():
        if normalized_answers.get(symbol) == correct_god:
            score += 1

    progress["checkpoint_answers"] = data
    progress["checkpoint_completed_at"] = str(datetime.datetime.now())
    progress["checkpoint_score"] = score
    progress["checkpoint_total"] = len(CHECKPOINT_ANSWER_KEY)
    progress["checkpoint_passed"] = score >= CHECKPOINT_MIN_SCORE

    progress = update_unlock_state(progress)
    session["learning_progress"] = progress

    return jsonify({
        "status": "ok",
        "checkpoint_score": score,
        "checkpoint_total": len(CHECKPOINT_ANSWER_KEY),
        "checkpoint_passed": progress["checkpoint_passed"],
        "unlock_state": progress["unlock_state"]
    })


@app.route("/start/quiz")
def start_quiz():
    progress = get_learning_progress()
    progress = update_unlock_state(progress)
    session["learning_progress"] = progress

    if not progress["unlock_state"]["quiz_unlocked"]:
        return redirect(url_for("learn_index"))

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


@app.route("/start/final")
def start_final():
    progress = get_learning_progress()
    progress = update_unlock_state(progress)
    session["learning_progress"] = progress

    if not progress["unlock_state"]["final_unlocked"]:
        return redirect(url_for("learn_index"))

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

    progress = get_learning_progress()
    progress["quiz_scores"][quiz_type] = {
        "score": score,
        "total": len(questions),
        "completed_at": str(datetime.datetime.now())
    }
    progress = update_unlock_state(progress)
    session["learning_progress"] = progress

    if quiz_type == "final" and score >= 8:
        return redirect(url_for("congrats", score=score, total=len(questions)))

    return render_template("results.html", score=score, total=len(questions),
                           breakdown=breakdown, retry_url=retry_url,
                           progress=progress, quiz_type=quiz_type)


@app.route("/congrats")
def congrats():
    score = request.args.get("score", 0, type=int)
    total = request.args.get("total", 10, type=int)
    return render_template("congrats.html", score=score, total=total)


@app.route('/quiz/<int:question_num>/check', methods=['POST'])
def quiz_check(question_num):
    data = load_questions()
    questions = data["quiz"]
    q = questions[question_num - 1]
    selected = request.get_json().get('answer', '').strip()
    correct = (selected == q['answer'])

    answers = session.get('quiz_answers', {})
    answers[str(question_num)] = selected
    session['quiz_answers'] = answers

    total = len(questions)
    next_url = url_for('quiz', question_num=question_num + 1) if question_num < total else url_for('results', quiz_type='quiz')
    return jsonify({'correct': correct, 'correct_answer': q['answer'], 'next_url': next_url})


@app.route('/final/<int:question_num>/check', methods=['POST'])
def final_check(question_num):
    data = load_questions()
    questions = data["final_quiz"]
    q = questions[question_num - 1]
    selected = request.get_json().get('answer', '').strip()

    if q.get('type') == 'text':
        correct = text_answer_is_correct(selected, q['answer'])
    else:
        correct = (selected == q['answer'])

    answers = session.get('final_answers', {})
    answers[str(question_num)] = selected
    session['final_answers'] = answers

    total = len(questions)
    next_url = url_for('final_quiz', question_num=question_num + 1) if question_num < total else url_for('results', quiz_type='final')
    correct_display = ', '.join(q['answer']) if isinstance(q['answer'], list) else q['answer']
    return jsonify({'correct': correct, 'correct_answer': correct_display, 'next_url': next_url})

@app.route("/learn/progress")
def learn_progress():
    progress = get_learning_progress()
    session["learning_progress"] = progress
    return jsonify(progress)


@app.route('/data/<path:filename>')
def data_files(filename):
    return send_from_directory('data', filename)




if __name__ == "__main__":
    app.run(debug=True)