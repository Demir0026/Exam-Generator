import pandas as pd
import json
import os
from models import Question
from database import add_question

def import_questions_from_excel(file) -> dict:
    """
    Reads an Excel file and imports questions into the database.
    Expected Columns: ['Ders', 'Zorluk', 'Soru Tipi', 'Soru', 'Cevap', 'Secenekler']
    Returns a status dict: {'success': int, 'errors': list}
    """
    status = {'success': 0, 'errors': []}
    
    try:
        df = pd.read_excel(file)
        
        df = pd.read_excel(file)
        
        required_cols = ['Ders', 'Zorluk', 'Soru']
        for col in required_cols:
            if col not in df.columns:
                return {'success': 0, 'errors': [f"Eksik Sütun: '{col}'. Lütfen şablonu kullanın."]}

        for index, row in df.iterrows():
            try:
                subject = str(row.get('Ders', '')).strip()
                difficulty = str(row.get('Zorluk', 'Easy')).strip()
                text = str(row.get('Soru', '')).strip()
                answer = str(row.get('Cevap', '')).strip()
                q_type_raw = str(row.get('Soru Tipi', 'Classic')).strip()
                
                # Check options column with fallback for Turkish characters
                options_raw = row.get('Secenekler')
                if pd.isna(options_raw):
                    options_raw = row.get('Seçenekler')
                if pd.isna(options_raw):
                    options_raw = row.get('Şeçenekler')
                
                has_options = pd.notna(options_raw) and str(options_raw).strip() != '' and str(options_raw).strip().lower() != 'nan'

                q_type_norm = q_type_raw.lower()
                if any(x in q_type_norm for x in ['seçmeli', 'secmeli', 'test', 'multiple', 'coktan', 'çoktan']):
                    q_type = 'Multiple Choice'
                elif has_options:
                    q_type = 'Multiple Choice'
                else:
                    q_type = 'Classic'

                # Process Options
                options = None
                if q_type == 'Multiple Choice':
                    if pd.notna(options_raw):
                        options_str = str(options_raw).strip()
                        
                        if '\n' in options_str:
                            delimiter = '\n'
                        elif ';' in options_str:
                            delimiter = ';'
                        else:
                            delimiter = ','
                            
                        options = [o.strip() for o in options_str.split(delimiter) if o.strip()]
                    
                    if not options:
                        status['errors'].append(f"UYARI (Satır {index+2}): '{text[:15]}...' sorusu Test olarak algılandı ama şık bulunamadı. Lütfen 'Secenekler' sütununu kontrol edin.")

                
                q = Question(
                    id=None,
                    text=text,
                    subject=subject,
                    difficulty=difficulty,
                    q_type=q_type,
                    options=json.dumps(options) if options else None,
                    answer=answer
                )
                add_question(q)
                status['success'] += 1
                
            except Exception as e:
                status['errors'].append(f"Satır {index+2} Hatası: {str(e)}")
                
    except Exception as e:
        status['errors'].append(f"Dosya Okuma Hatası: {str(e)}")
        
    return status

def create_template_excel(filename="soru_sablonu.xlsx"):
    """Creates a sample Excel file for the user."""
    data = [
        {
            "Ders": "Matematik",
            "Zorluk": "Kolay", 
            "Soru Tipi": "Klasik",
            "Soru": "2+2 kaç eder?",
            "Cevap": "4",
            "Secenekler": ""
        },
        {
            "Ders": "Tarih",
            "Zorluk": "Orta", 
            "Soru Tipi": "Çoktan Seçmeli",
            "Soru": "İstanbul kaç yılında fethedildi?",
            "Cevap": "1453",
            "Secenekler": "1071, 1299, 1453, 1923"
        }
    ]
import io

def create_template_excel():
    """Creates a sample Excel file in memory for the user."""
    data = [
        {
            "Ders": "Matematik",
            "Zorluk": "Kolay", 
            "Soru Tipi": "Klasik",
            "Soru": "2+2 kaç eder?",
            "Cevap": "4",
            "Seçenekler": ""
        },
        {
            "Ders": "Tarih",
            "Zorluk": "Orta", 
            "Soru Tipi": "Çoktan Seçmeli",
            "Soru": "İstanbul kaç yılında fethedildi?",
            "Cevap": "1453",
            "Seçenekler": "1071; 1299; 1453; 1923"
        }
    ]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return output
