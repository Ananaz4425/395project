from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from datetime import datetime, date, timedelta

app = Flask(__name__)

@app.context_processor
def inject_globals():
    conn = get_db()
    today = date.today().isoformat()
    pending = conn.execute(
        "SELECT COUNT(*) FROM deadlines WHERE status != 'Done' AND due_date >= ?", (today,)
    ).fetchone()[0]
    conn.close()
    return {'now': datetime.now(), 'pending_count': pending}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "database.db")


# ─────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    sql_path = os.path.join(BASE_DIR, "database.sql")
    with open(sql_path, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# HOME / DASHBOARD
# ─────────────────────────────────────────
@app.route("/")
def home():
    conn = get_db()

    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    today = date.today().isoformat()

    # Stats
    logs         = conn.execute("SELECT * FROM health_log ORDER BY date DESC LIMIT 7").fetchall()
    total_logs   = conn.execute("SELECT COUNT(*) FROM health_log").fetchone()[0]
    active_goals = conn.execute("SELECT COUNT(*) FROM goals WHERE status='Active'").fetchone()[0]
    pending_deadlines = conn.execute(
        "SELECT COUNT(*) FROM deadlines WHERE status != 'Done' AND due_date >= ?", (today,)
    ).fetchone()[0]
    urgent_deadlines = conn.execute(
        "SELECT * FROM deadlines WHERE status != 'Done' ORDER BY due_date ASC LIMIT 4"
    ).fetchall()

    # Random affirmation
    affirmation = conn.execute(
        "SELECT * FROM affirmations WHERE is_favorite=1 ORDER BY RANDOM() LIMIT 1"
    ).fetchone()
    if not affirmation:
        affirmation = conn.execute("SELECT * FROM affirmations ORDER BY RANDOM() LIMIT 1").fetchone()

    # Wellbeing score from last 7 logs
    wellbeing = 0
    if logs:
        mood_map   = {"Great": 4, "Good": 3, "Okay": 2, "Bad": 1}
        energy_map = {"High": 3, "Medium": 2, "Low": 1}
        n = len(logs)
        avg_sleep  = sum(r["sleep_hours"]  or 0 for r in logs) / n
        avg_water  = sum(r["water_intake"] or 0 for r in logs) / n
        avg_mood   = sum(mood_map.get(r["mood"],   2) for r in logs) / n
        avg_energy = sum(energy_map.get(r["energy"], 2) for r in logs) / n
        wellbeing  = round(
            (avg_sleep / 9 * 25) + (avg_water / 3 * 25) +
            (avg_mood  / 4 * 25) + (avg_energy / 3 * 25), 1
        )

    # Active goals list for dashboard widget
    active_goals_list = conn.execute(
        "SELECT * FROM goals WHERE status='Active' ORDER BY priority DESC, deadline ASC LIMIT 4"
    ).fetchall()

    # This week's logs (Mon–Sun) for streak widget
    today_dt = date.today()
    monday   = today_dt - timedelta(days=today_dt.weekday())
    week_logs = []
    for i in range(7):
        day = (monday + timedelta(days=i)).isoformat()
        row = conn.execute("SELECT * FROM health_log WHERE date=? LIMIT 1", (day,)).fetchone()
        week_logs.append(row)

    streak = sum(1 for r in week_logs if r and r["exercise"])

    # Today's log for hydration widget
    today_log = conn.execute(
        "SELECT * FROM health_log WHERE date=? LIMIT 1", (today,)
    ).fetchone()

    conn.close()
    return render_template("home.html",
        greeting=greeting,
        today=today,
        total_logs=total_logs,
        active_goals=active_goals,
        pending_deadlines=pending_deadlines,
        urgent_deadlines=urgent_deadlines,
        affirmation=affirmation,
        wellbeing=wellbeing,
        streak=streak,
        recent_logs=logs,
        active_goals_list=active_goals_list,
        week_logs=week_logs,
        today_log=today_log,
    )


# ─────────────────────────────────────────
# HEALTH LOG — CRUD
# ─────────────────────────────────────────
@app.route("/health")
def health_list():
    conn = get_db()
    records = conn.execute("SELECT * FROM health_log ORDER BY date DESC").fetchall()
    total = len(records)
    avg_sleep = avg_water = wellbeing = 0
    mood_counts = {"Great": 0, "Good": 0, "Okay": 0, "Bad": 0}
    if total:
        mood_map   = {"Great": 4, "Good": 3, "Okay": 2, "Bad": 1}
        avg_sleep  = round(sum(r["sleep_hours"]  or 0 for r in records) / total, 1)
        avg_water  = round(sum(r["water_intake"] or 0 for r in records) / total, 1)
        avg_mood   = sum(mood_map.get(r["mood"], 2) for r in records) / total
        wellbeing  = round((avg_sleep/9*35) + (avg_water/3*35) + (avg_mood/4*30), 1)
        for r in records:
            if r["mood"] in mood_counts:
                mood_counts[r["mood"]] += 1
    conn.close()
    return render_template("health_list.html",
        records=records, total=total,
        avg_sleep=avg_sleep, avg_water=avg_water,
        wellbeing=wellbeing, mood_counts=mood_counts
    )


@app.route("/health/add", methods=["GET", "POST"])
def health_add():
    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO health_log (date, mood, energy, sleep_hours, water_intake, exercise, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("date"),
            request.form.get("mood"),
            request.form.get("energy"),
            float(request.form.get("sleep") or 0),
            float(request.form.get("water") or 0),
            request.form.get("exercise"),
            request.form.get("notes"),
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("health_list"))
    return render_template("health_add.html", today=date.today().isoformat())


@app.route("/health/edit/<int:id>", methods=["GET", "POST"])
def health_edit(id):
    conn = get_db()
    if request.method == "POST":
        conn.execute("""
            UPDATE health_log SET date=?, mood=?, energy=?, sleep_hours=?,
            water_intake=?, exercise=?, notes=? WHERE id=?
        """, (
            request.form.get("date"), request.form.get("mood"),
            request.form.get("energy"),
            float(request.form.get("sleep") or 0),
            float(request.form.get("water") or 0),
            request.form.get("exercise"), request.form.get("notes"), id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("health_list"))
    record = conn.execute("SELECT * FROM health_log WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("health_edit.html", record=record)


@app.route("/health/delete/<int:id>")
def health_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM health_log WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("health_list"))


# ─────────────────────────────────────────
# GOALS — CRUD
# ─────────────────────────────────────────
@app.route("/goals")
def goals_list():
    conn = get_db()
    goals = conn.execute("SELECT * FROM goals ORDER BY priority DESC, deadline ASC").fetchall()
    conn.close()
    return render_template("goals_list.html", goals=goals)


@app.route("/goals/add", methods=["GET", "POST"])
def goals_add():
    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO goals (title, category, description, deadline, status, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("title"), request.form.get("category"),
            request.form.get("description"), request.form.get("deadline"),
            request.form.get("status", "Active"), request.form.get("priority", "Medium")
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("goals_list"))
    return render_template("goals_add.html")


@app.route("/goals/edit/<int:id>", methods=["GET", "POST"])
def goals_edit(id):
    conn = get_db()
    if request.method == "POST":
        conn.execute("""
            UPDATE goals SET title=?, category=?, description=?,
            deadline=?, status=?, priority=? WHERE id=?
        """, (
            request.form.get("title"), request.form.get("category"),
            request.form.get("description"), request.form.get("deadline"),
            request.form.get("status"), request.form.get("priority"), id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("goals_list"))
    goal = conn.execute("SELECT * FROM goals WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("goals_edit.html", goal=goal)


@app.route("/goals/delete/<int:id>")
def goals_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM goals WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("goals_list"))


@app.route("/goals/complete/<int:id>")
def goals_complete(id):
    conn = get_db()
    conn.execute("UPDATE goals SET status='Completed' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("goals_list"))


# ─────────────────────────────────────────
# AFFIRMATIONS — CRUD
# ─────────────────────────────────────────
@app.route("/affirmations")
def affirmations_list():
    conn = get_db()
    items = conn.execute("SELECT * FROM affirmations ORDER BY is_favorite DESC, created_at DESC").fetchall()
    conn.close()
    return render_template("affirmations_list.html", items=items)


@app.route("/affirmations/add", methods=["GET", "POST"])
def affirmations_add():
    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO affirmations (text, category, is_favorite) VALUES (?, ?, ?)
        """, (
            request.form.get("text"), request.form.get("category"),
            1 if request.form.get("is_favorite") else 0
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("affirmations_list"))
    return render_template("affirmations_add.html")


@app.route("/affirmations/delete/<int:id>")
def affirmations_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM affirmations WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("affirmations_list"))


@app.route("/affirmations/toggle/<int:id>")
def affirmations_toggle(id):
    conn = get_db()
    conn.execute("UPDATE affirmations SET is_favorite = 1 - is_favorite WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("affirmations_list"))


# ─────────────────────────────────────────
# DEADLINES — CRUD
# ─────────────────────────────────────────
@app.route("/deadlines")
def deadlines_list():
    conn = get_db()
    today = date.today().isoformat()
    deadlines = conn.execute("""
        SELECT *,
        CASE WHEN due_date < ? AND status != 'Done' THEN 1 ELSE 0 END as overdue
        FROM deadlines ORDER BY
        CASE status WHEN 'Done' THEN 1 ELSE 0 END ASC,
        due_date ASC
    """, (today,)).fetchall()
    conn.close()
    return render_template("deadlines_list.html", deadlines=deadlines, today=today)


@app.route("/deadlines/add", methods=["GET", "POST"])
def deadlines_add():
    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO deadlines (title, subject, due_date, priority, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("title"), request.form.get("subject"),
            request.form.get("due_date"), request.form.get("priority", "Medium"),
            request.form.get("status", "Pending"), request.form.get("notes")
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("deadlines_list"))
    return render_template("deadlines_add.html")


@app.route("/deadlines/edit/<int:id>", methods=["GET", "POST"])
def deadlines_edit(id):
    conn = get_db()
    if request.method == "POST":
        conn.execute("""
            UPDATE deadlines SET title=?, subject=?, due_date=?,
            priority=?, status=?, notes=? WHERE id=?
        """, (
            request.form.get("title"), request.form.get("subject"),
            request.form.get("due_date"), request.form.get("priority"),
            request.form.get("status"), request.form.get("notes"), id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("deadlines_list"))
    dl = conn.execute("SELECT * FROM deadlines WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("deadlines_edit.html", dl=dl)


@app.route("/deadlines/delete/<int:id>")
def deadlines_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM deadlines WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("deadlines_list"))


@app.route("/deadlines/done/<int:id>")
def deadlines_done(id):
    conn = get_db()
    conn.execute("UPDATE deadlines SET status='Done' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("deadlines_list"))


# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    app.run(debug=True)