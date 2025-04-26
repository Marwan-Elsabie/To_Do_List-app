import datetime
import uuid
import os
from pathlib import Path
from datetime import datetime, date

TODO_DIR = Path(__file__).parent
FILENAME = TODO_DIR / "Todo.txt"

DEFAULT_CATEGORIES = {
    'work': '#FF5252',      # Red
    'personal': '#4CAF50',  # Green
    'shopping': '#FFC107',  # Amber
    'finance': '#2196F3',   # Blue
    'other': '#9E9E9E'      # Grey
}

def load_tasks(user_id):
    user_file = f"tasks_{user_id}.txt"
    
    tasks = []
    try:
        with open(FILENAME, "r") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                
                task = {
                    "done": False,
                    "task": "",
                    "priority": "Medium",
                    "due_date": None,
                    "tags": [],  
                    "id": str(uuid.uuid4()),
                    'category': 'other'
                }
                
                if line.startswith("[x]"):
                    task["done"] = True
                    line = line[3:].strip()
                elif line.startswith("[ ]"):
                    line = line[3:].strip()
                
                parts = line.split(" | ")
                task["task"] = parts[0]
                
                for part in parts[1:]:
                    if part.startswith("priority="):
                        task["priority"] = part[9:]  
                    elif part.startswith("due="):
                        task["due_date"] = part[4:]  
                    elif part.startswith("id="):
                        task["id"] = part[3:]  
                    elif part.startswith("tags="):
                         task["tags"] = [t.strip() for t in part[5:].split(",") if t.strip()]
                    elif part.startswith("category="):
                        task["category"] = part[9:] 
                
                
                if not task.get("id"):
                    task["id"] = str(uuid.uuid4())

                if "tags" not in task:
                    task["tags"] = []
                
                tasks.append(task)
                
    except FileNotFoundError:
        return []
    
    return tasks


def save_tasks(user_id, tasks):
    user_file = f"tasks_{user_id}.txt"
    try:
        with open(FILENAME, "w") as file:
            for task in tasks:
                status = "[x]" if task["done"] else "[ ]"
                line = f"{status} {task['task']}"
                
                line += f" | category={task.get('category', 'other')}"
                
                if task.get("priority"):
                    line += f" | priority={task['priority']}"
                if task.get("due_date"):
                    line += f" | due={task['due_date']}"
                if task.get("id"):
                    line += f" | id={task['id']}"
                if task.get("tags"):
                   line += f" | tags={','.join(task['tags'])}"
                
                file.write(line + "\n")
                print(f"Saving {len(tasks)} tasks")
    except IOError as e:
        print(f"Error saving tasks: {e}")

def sort_tasks(tasks):
    tasks_with_due = []
    tasks_without_due = []

    for task in tasks:
        due = task.get("due_date")
        if due and due != "No due date":
            try:
                
                datetime.strptime(due, "%Y-%m-%d")
                tasks_with_due.append(task)
            except ValueError:
                tasks_without_due.append(task)
        else:
            tasks_without_due.append(task)

    
    tasks_with_due.sort(key=lambda x: datetime.strptime(x['due_date'], "%Y-%m-%d"))
    return tasks_with_due + tasks_without_due

def validate_task(task):
    required_fields = ["task", "id"]
    for field in required_fields:
        if field not in task or not task[field]:
            return False
    
    if task["priority"] not in ["Low", "Medium", "High"]:
        return False
        
    if task["due_date"] and task["due_date"] != "No due date":
        try:
            datetime.strptime(task["due_date"], "%Y-%m-%d")
        except ValueError:
            return False
            
    return True
        
def get_due_status(due_date):
    if due_date in [None, "No due date"]:
        return ""
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
        today = date.today()  
        delta = (due - today).days
        
        if delta < 0:
            return "overdue"
        elif delta == 0:
            return "due-today"
        elif delta <= 3:
            return "due-soon"
        return ""
    except ValueError:
        return ""
    
def validate_date(date_str):
    if date_str in [None, "", "No due date"]:
        return True
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False