import sqlite3
import json
from typing import List, Optional
from models import Question, Exam
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "exam_generator.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            subject TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            q_type TEXT NOT NULL,
            options TEXT,
            answer TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            title TEXT,
            question_ids TEXT -- Comma separated IDs
        )
    ''')
    
    conn.commit()
    conn.close()

def clear_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM questions')
    cursor.execute('DELETE FROM exams')
    conn.commit()
    conn.close()

def add_question(q: Question):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO questions (text, subject, difficulty, q_type, options, answer)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (q.text, q.subject, q.difficulty, q.q_type, q.options, q.answer))
    conn.commit()
    conn.close()

def delete_question(question_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()

def get_all_questions() -> List[Question]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM questions')
    rows = cursor.fetchall()
    conn.close()
    
    questions = []
    for row in rows:
        questions.append(Question(
            id=row[0],
            text=row[1],
            subject=row[2],
            difficulty=row[3],
            q_type=row[4],
            options=row[5],
            answer=row[6]
        ))
    return questions

def get_questions_by_criteria(subject: str = None, difficulty: str = None) -> List[Question]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT * FROM questions WHERE 1=1"
    params = []
    
    if subject:
        query += " AND trim(lower(subject)) = trim(lower(?))"
        params.append(subject.strip())
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    questions = []
    for row in rows:
        questions.append(Question(
            id=row[0],
            text=row[1],
            subject=row[2],
            difficulty=row[3],
            q_type=row[4],
            options=row[5],
            answer=row[6]
        ))
    return questions

def get_unique_subjects() -> List[str]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT subject FROM questions')
    rows = cursor.fetchall()
    conn.close()
    
    subjects = sorted([row[0] for row in rows if row[0]])
    return subjects

def save_exam(exam: Exam):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    q_ids = ",".join([str(q.id) for q in exam.questions if q.id is not None])
    
    cursor.execute('''
        INSERT INTO exams (title, question_ids, created_at)
        VALUES (?, ?, ?)
    ''', (exam.title, q_ids, exam.created_at))
    conn.commit()
    conn.close()

def get_all_exams():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, created_at, title FROM exams ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_exam_by_id(exam_id: int) -> Optional[Exam]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, created_at, title, question_ids FROM exams WHERE id = ?', (exam_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
        
    exam_id, created_at, title, q_ids_str = row
    
    if not q_ids_str:
        return Exam(id=exam_id, created_at=created_at, title=title, questions=[])

    question_ids = [int(id_str) for id_str in q_ids_str.split(',') if id_str.strip()]
    
    all_qs = {q.id: q for q in get_all_questions()}
    
    exam_questions = []
    for q_id in question_ids:
        if q_id in all_qs:
            exam_questions.append(all_qs[q_id])
            
    conn.close()
    
    return Exam(
        id=exam_id,
        created_at=created_at, 
        title=title,
        questions=exam_questions
    )

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
