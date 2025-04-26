from flask import Flask, render_template, request, redirect, url_for, flash, jsonify 
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime, date

load_dotenv() 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'your-very-secret-key-here')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Make sure this points to your login route name
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    tasks = db.relationship('Task', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), default='Medium')
    due_date = db.Column(db.Date)
    category = db.Column(db.String(20), default='other')
    tags = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)
    position = db.Column(db.Integer, default=0)

    def __init__(self, **kwargs):
        super(Task, self).__init__(**kwargs)
        
        if self.position is None:
            last_task = Task.query.order_by(Task.position.desc()).first()
            self.position = (last_task.position + 1) if last_task else 0

    def to_dict(self):
        return {
            'id': self.id,
            'task': self.title,
            'done': self.done,
            'priority': self.priority,
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'category': self.category,
            'tags': self.tags.split(',') if self.tags else [],
            'user_id': self.user_id
        }
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# User loader callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect already authenticated users
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Main Application Routes
@app.route('/')
@login_required
def index():
    tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.deleted_at.is_(None)
    ).order_by(Task.position).all()
    task_list = [task.to_dict() for task in tasks]
    

    # Filtering logic
    filter_type = request.args.get('filter', 'all')
    tag_filter = request.args.get('tag', '').strip().lower()
    
    filtered_tasks = []
    for task in task_list:
        # Status filter
        status_match = True
        if filter_type == 'active':
            status_match = not task['done']
        elif filter_type == 'completed':
            status_match = task['done']
        elif filter_type in ['high', 'medium', 'low']:
            status_match = task['priority'].lower() == filter_type.lower()
        
        # Tag filter
        tag_match = True
        if tag_filter:
            tag_match = False
            if task['tags']:
                for tag in task['tags']:
                    if tag_filter in tag.lower():
                        tag_match = True
                        break
        
        if status_match and tag_match:
            filtered_tasks.append(task)
    
    stats = calculate_stats(filtered_tasks)
    return render_template('index.html', 
                         tasks=filtered_tasks, 
                         stats=stats,
                         current_filter=filter_type,
                         current_tag=tag_filter,
                         username=current_user.username)

# Task Routes
@app.route("/add", methods=["POST"])
@login_required
def add():
    task_text = request.form.get("task", "").strip()
    if not task_text:
        flash("Task description cannot be empty", "error")
        return redirect(url_for('index'))
    
    
    due_date_str = request.form.get("due_date")
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD", "error")
            return redirect(url_for('index'))
    
    
    tags = request.form.get("tags", "").strip()
    
    
    new_task = Task(
        title=task_text,
        priority=request.form.get("priority", "Medium"),
        due_date=due_date,
        category=request.form.get("category", "other"),
        tags=tags,
        user_id=current_user.id  
    )
    
    try:
        db.session.add(new_task)
        db.session.commit()
        flash("Task added successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error saving task", "error")
        app.logger.error(f"Error saving task: {e}")
    
    return redirect(url_for('index'))

@app.route("/toggle/<task_id>")
@login_required
def toggle(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.done = not task.done
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/delete/<task_id>")
@login_required
def delete(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    
    task.deleted_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Task deleted. <a href="/undo_delete/{task.id}" class="undo-link">Undo</a>', 'info')
    return redirect(url_for('index'))

@app.route("/undo_delete/<task_id>")
@login_required
def undo_delete(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.deleted_at = None
    db.session.commit()
    flash('Task restored!', 'success')
    return redirect(url_for('index'))

@app.route("/edit/<task_id>", methods=["GET", "POST"])
@login_required
def edit(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    if request.method == "POST":
        task.title = request.form["task"].strip()
        task.priority = request.form.get("priority", "Medium")
        due_date_str = request.form.get("due_date")
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        task.category = request.form.get("category", "other")
        task.tags = request.form.get("tags", "")
        
        db.session.commit()
        flash("Task updated successfully", "success")
        return redirect(url_for('index'))
    
    return render_template("edit.html", task=task.to_dict())

@app.route('/reorder-tasks', methods=['POST'])
@login_required
def reorder_tasks():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
        
    try:
        new_order = request.json.get('order', [])
        
        
        user_tasks = {t.id: t for t in Task.query.filter_by(user_id=current_user.id).all()}
        invalid_tasks = [tid for tid in new_order if tid not in user_tasks]
        
        if invalid_tasks:
            return jsonify({
                'error': f'Invalid task IDs: {invalid_tasks}',
                'success': False
            }), 403
            
        for position, task_id in enumerate(new_order):
            user_tasks[task_id].position = position
                
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Utility Functions
def calculate_stats(tasks):
    stats = {
        'total': len(tasks),
        'active': 0,
        'completed': 0,
        'overdue': 0
    }
    
    today = date.today()
    for task in tasks:
        if task.get('done'):
            stats['completed'] += 1
        else:
            stats['active'] += 1
            if task.get('due_date'):
                due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                if due_date < today:
                    stats['overdue'] += 1
    return stats

@app.context_processor
def inject_utilities():
    def get_due_status(due_date):
        if not due_date or due_date == 'No due date':
            return ''
        try:
            due = datetime.strptime(due_date, '%Y-%m-%d').date()
            today = date.today()
            if due < today:
                return 'overdue'
            elif due == today:
                return 'due-today'
            elif (due - today).days <= 3:
                return 'due-soon'
            return ''
        except ValueError:
            return ''
    
    return {
        'datetime': datetime,
        'date': date,
        'get_due_status': get_due_status,
        'categories': {
            'work': '#FF5252',
            'personal': '#4CAF50',
            'shopping': '#FFC107',
            'finance': '#2196F3',
            'other': '#9E9E9E'
        },
        'default_theme': 'light'
    }

# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Create database tables
with app.app_context():
    db.create_all()
    
    # Create default admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)