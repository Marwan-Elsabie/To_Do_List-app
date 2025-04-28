# 📝 Flask To-Do List Application

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

A full-featured task management web application with user authentication, dark mode, and drag-and-drop functionality.

## ✨ Features

- 🔒 User authentication (Login/Register/Logout)
- 🌓 Light/Dark mode toggle
- 🗃️ Task management (Create/Edit/Delete)
- 🏷️ Categorization (Work/Personal/Shopping/Finance/Other)
- 🔼🔽 Drag-and-drop reordering
- ⏰ Due dates with visual indicators
- ✅ Mark tasks as complete
- 🔍 Filtering by status/category

## 🚀 Live Demo

[Try it live here!](https://marwan777.pythonanywhere.com/login?next=%2F) 

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Marwan-Elsabie/To_Do_List-app.git
   cd To_Do_List-app
2.Set up virtual environment:
  python -m venv venv
  # Windows:
  venv\Scripts\activate
  # Mac/Linux:
  source venv/bin/activate
3. Install dependencies:
  pip install -r requirements.txt
4. Configure environment:
  # Create a .env file (copy from example if available)
  # Or create manually:
  echo "SECRET_KEY=your-secret-key-here" > .env
  echo "DATABASE_URL=sqlite:///instance/tasks.db" >> .env
5. Run the application:
   # For standard app.py structure:
  flask --app app run
  
  # Or alternatively:
  python app.py
6. Access the app:
  Open http://localhost:5000 in your browser
