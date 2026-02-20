import random
from database import get_questions_by_criteria
from models import Exam, Question
from datetime import datetime

DIFFICULTY_WEIGHTS = {
    'Easy': 1,
    'Medium': 3,
    'Hard': 5
}

TARGET_RANGES = {
    'Easy': (1.0, 2.3),
    'Medium': (2.3, 3.8),
    'Hard': (3.8, 5.0)
}

def calculate_average_difficulty(questions):
    if not questions:
        return 0
    total = sum(DIFFICULTY_WEIGHTS.get(q.difficulty, 3) for q in questions)
    return total / len(questions)

def generate_exam(title, criteria_list):
    """
    Generates an exam based on weighted difficulty averages.
    """
    selected_questions = []
    
    for criteria in criteria_list:
        subject = criteria.get('subject')
        target_diff_str = criteria.get('difficulty')
        count = criteria.get('count', 1)
        
        all_questions = get_questions_by_criteria(subject, None)
        
        if len(all_questions) < count:
            print(f"Warning: Not enough questions for {subject}. Requested {count}, found {len(all_questions)}.")
            selected_questions.extend(all_questions)
            continue
            
        target_min, target_max = TARGET_RANGES.get(target_diff_str, (1.0, 5.0))
        best_sample = None
        best_avg_dist = float('inf')
        
        found_match = False

        for _ in range(100):
            sample = random.sample(all_questions, count)
            avg = calculate_average_difficulty(sample)
            
            if target_min <= avg <= target_max:
                selected_questions.extend(sample)
                found_match = True
                print(f"Match found for {subject} ({target_diff_str}): Avg {avg:.2f}")
                break
            
            target_center = (target_min + target_max) / 2
            dist = abs(avg - target_center)
            if dist < best_avg_dist:
                best_avg_dist = dist
                best_sample = sample
        
        if not found_match:
             print(f"Could not find exact difficulty match for {subject} ({target_diff_str}). Using closest match.")
             selected_questions.extend(best_sample)
            
    exam = Exam(
        id=None,
        created_at=datetime.now(),
        title=title,
        questions=selected_questions
    )
    return exam
