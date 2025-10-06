from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'todo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ✅ Local timezone (India Standard Time)
LOCAL_TZ = ZoneInfo("Asia/Kolkata")

# ---------- Model ----------
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # stored in UTC
    due_at = db.Column(db.DateTime, nullable=True)               # stored in UTC
    overdue = db.Column(db.Boolean, default=False)               # ✅ new field

with app.app_context():
    db.create_all()

# ---------- Routes ----------
@app.route('/')
def index():
    now_utc = datetime.utcnow()
    tasks_raw = Task.query.all()

    # ✅ Update overdue field in DB
    for task in tasks_raw:
        if task.due_at and not task.completed and task.due_at < now_utc:
            task.overdue = True
        else:
            task.overdue = False
    db.session.commit()

    tasks = []
    for t in tasks_raw:
        created_local = t.created_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(LOCAL_TZ)
        created_str = created_local.strftime("%d-%m-%Y %I:%M %p")

        if t.due_at:
            due_local = t.due_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(LOCAL_TZ)
            due_str = due_local.strftime("%d-%m-%Y %I:%M %p")
        else:
            due_str = None

        tasks.append({
            "id": t.id,
            "content": t.content,
            "completed": t.completed,
            "created_str": created_str,
            "due_str": due_str,
            "overdue": t.overdue
        })

    # ✅ Overdue tasks appear on top
    tasks_sorted = sorted(tasks, key=lambda x: (not x["overdue"], x["created_str"]))

    overdue_tasks = [t for t in tasks_sorted if t["overdue"]]
    normal_tasks = [t for t in tasks_sorted if not t["overdue"]]
    
    return render_template('index.html', overdue_tasks=overdue_tasks, normal_tasks=normal_tasks)

@app.route('/add', methods=['POST'])
def add_task():
    content = request.form.get('content', '').strip()
    due_at_str = request.form.get('due_at', '').strip()
    if not content:
        return redirect(url_for('index'))

    due_utc = None
    if due_at_str:
        try:
            # interpret as IST local → convert to UTC
            due_local = datetime.strptime(due_at_str, '%Y-%m-%dT%H:%M')
            due_utc = due_local.replace(tzinfo=LOCAL_TZ).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        except Exception:
            due_utc = None

    new_task = Task(content=content, due_at=due_utc)
    db.session.add(new_task)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = not task.completed
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
