import streamlit as st
import pandas as pd
import json
import os
from database import get_all_questions, add_question, get_unique_subjects, delete_question, save_exam, get_all_exams, get_exam_by_id
from generator import generate_exam
from exporter import export_to_pdf, export_to_docx
from importer import import_questions_from_excel, create_template_excel
from models import Question, Exam

st.set_page_config(page_title="Sınav Oluşturucu", page_icon="📝", layout="wide")
st.title("📝 Sınav Oluşturucu")

# Tabs
tab1, tab2, tab3 = st.tabs(["Soru Havuzu", "Sınav Oluştur", "Sınav Geçmişi"])

with tab1:
    st.header("Soru Yönetimi")
    
    with st.expander("📂 Excel'den Toplu Yükle"):
        st.info("Soruları Excel dosyasından topluca yükleyebilirsiniz. Önce şablonu indirip doldurun.")
        
        col_dl, col_up = st.columns([1, 2])
        with col_dl:
            excel_buffer = create_template_excel()
            st.download_button(
                label="📥 Örnek Şablonu İndir",
                data=excel_buffer,
                file_name="soru_yukleme_sablonu.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        uploaded_file = st.file_uploader("Excel Dosyanızı Buraya Sürükleyin", type=["xlsx"])
        if uploaded_file:
            if st.button("Yüklemeyi Başlat", type="primary"):
                with st.spinner("Sorular işleniyor..."):
                    status = import_questions_from_excel(uploaded_file)
                    
                    if status['success'] > 0:
                        st.success(f"✅ {status['success']} soru başarıyla veritabanına eklendi!")
                    
                    if status['errors']:
                        st.error(f"{len(status['errors'])} adet hata oluştu.")
                        with st.expander("Hata Detayları"):
                            for err in status['errors']:
                                st.write(f"- {err}")
                                
                    if status['success'] > 0:
                        import time
                        time.sleep(1) # Let user see success message
                        st.rerun()

    with st.expander("➕ Elle Yeni Soru Ekle"):
        with st.form("add_question_form"):
            col1, col2 = st.columns(2)
            with col1:
                subject = st.text_input("Ders (Örn: Matematik)")
                difficulty = st.selectbox("Zorluk", ["Easy", "Medium", "Hard"])
            with col2:
                q_type = st.selectbox("Soru Tipi", ["Multiple Choice", "Classic"])
                answer = st.text_input("Doğru Cevap")
            
            text = st.text_area("Soru Metni")
            
            options = None
            if q_type == "Multiple Choice":
                st.info("ℹ️ Seçenekleri birbirinden ayırmak için **her seçeneği yeni bir satıra yazın** (Enter tuşu ile).")
                options_str = st.text_area("Seçenekler", height=100, help="Örn:\n5\n6\n7")
                if options_str:
                    options = [opt.strip() for opt in options_str.split('\n') if opt.strip()]
                    if len(options) == 1 and " " in options[0]:
                        st.warning("⚠️ Tek bir seçenek algılandı ama içinde boşluklar var. Her birini alt alta yazdığınızdan emin olun.")
                    elif len(options) > 0:
                        st.caption(f"✅ {len(options)} seçenek algılandı: " + ", ".join([f"[{o}]" for o in options]))
            
            submitted = st.form_submit_button("Soru Ekle")
            if submitted:
                if text and subject:
                    # Save to DB
                    q = Question(
                        id=None, 
                        text=text.strip(), 
                        subject=subject.strip(), 
                        difficulty=difficulty, 
                        q_type=q_type, 
                        options=json.dumps(options) if options else None, 
                        answer=answer
                    )
                    add_question(q)
                    st.success("Soru başarıyla eklendi!")
                    st.rerun()
                else:
                    st.error("Lütfen soru metni ve ders alanlarını doldurun.")

    st.markdown("---")
    questions = get_all_questions()
    
    if questions:
        st.subheader(f"📋 Mevcut Sorular ({len(questions)})")
        
        for q in reversed(questions):
            with st.expander(f"#{q.id} | {q.subject} ({q.difficulty})"):
                col_info, col_act = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**Soru:** {q.text}")
                    st.markdown(f"**Cevap:** {q.answer}")
                    if q.options:
                        try:
                            options_list = json.loads(q.options)
                            st.caption("Seçenekler:")
                            for opt in options_list:
                                st.caption(f"- {opt}")
                        except:
                            st.caption(f"Seçenekler: {q.options}")
                with col_act:
                    if st.button("🗑️ Sil", key=f"del_{q.id}", type="primary"):
                        delete_question(q.id)
                        st.success("Silindi!")
                        st.rerun()
    else:
        st.info("Henüz soru eklenmemiş.")

with tab2:
    st.header("Sınav Oluştur")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Ayarlar")
        with st.form("exam_form"):
            exam_title = st.text_input("Sınav Başlığı", value="Final Sınavı")
            
            valid_subjects = get_unique_subjects()
            if valid_subjects:
                c_subject = st.selectbox("Ders Seçiniz", valid_subjects)
            else:
                c_subject = st.text_input("Ders", placeholder="Math")
            
            c_difficulty = st.selectbox("Zorluk Seviyesi", ["Easy", "Medium", "Hard"], key="c_diff")
            c_count = st.number_input("Soru Sayısı", min_value=1, value=5)
            
            generate_btn = st.form_submit_button("Sınavı Oluştur", type="primary")
            
            if generate_btn:
                criteria = [{
                    "subject": c_subject.strip(),
                    "difficulty": c_difficulty,
                    "count": c_count
                }]
                
                try:
                    exam = generate_exam(exam_title, criteria)
                    save_exam(exam) # Save to DB
                    st.session_state.last_exam = exam
                    st.success(f"Sınav oluşturuldu! Toplam {len(exam.questions)} soru.")
                except Exception as e:
                    st.error(f"Hata: {e}")

    with col2:
        st.subheader("Önizleme ve Çıktı")
        
        if 'last_exam' in st.session_state:
            exam = st.session_state.last_exam
            
            # Preview
            with st.expander("Sınav Önizlemesi", expanded=True):
                st.markdown(f"### {exam.title}")
                st.info(f"Oluşturulan sınavda toplam {len(exam.questions)} soru var.")
                
                if len(exam.questions) == 0:
                    st.warning("⚠️ Hiç soru bulunamadı! Kriterlerinize uygun soru olmayabilir veya veritabanı boş.")
                
                for i, q in enumerate(exam.questions, 1):
                    st.markdown(f"**{i}. {q.text}**")
                    st.caption(f"[{q.subject} - {q.difficulty}]")
                    if q.q_type == "Multiple Choice" and q.options:
                        try:
                            opts = json.loads(q.options)
                            for opt in opts:
                                st.write(f"- {opt}")
                        except:
                            pass
                    st.divider()
            
            # Export Buttons
            col_d, col_p = st.columns(2)
            with col_d:
                if st.button("Word Olarak İndir"):
                    filename = "generated_exam.docx"
                    export_to_docx(exam, filename)
                    with open(filename, "rb") as f:
                        st.download_button("Dosyayı İndir (DOCX)", f, file_name=filename, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
            with col_p:
                if st.button("PDF Olarak İndir"):
                    filename = "generated_exam.pdf"
                    export_to_pdf(exam, filename)
                    with open(filename, "rb") as f:
                        st.download_button("Dosyayı İndir (PDF)", f, file_name=filename, mime="application/pdf")

with tab3:
    st.header("Geçmiş Sınavlar")
    exams = get_all_exams()
    
    if not exams:
        st.info("Henüz kaydedilmiş bir sınav yok.")
    else:
        # Select Exam
        exam_options = {f"#{ex[0]} - {ex[2]} ({ex[1][:16]})": ex[0] for ex in exams}
        selected_option = st.selectbox("Görüntülemek istediğiniz sınavı seçin:", list(exam_options.keys()))
        
        if selected_option:
            selected_id = exam_options[selected_option]
            
            if st.button("Sınavı Görüntüle", type="primary"):
                loaded_exam = get_exam_by_id(selected_id)
                if loaded_exam:
                     st.session_state.history_exam = loaded_exam
                else:
                    st.error("Sınav verisi yüklenemedi.")

        # Show Loaded Exam
        if 'history_exam' in st.session_state:
            h_exam = st.session_state.history_exam
            
            st.markdown("---")
            st.subheader(f"📄 {h_exam.title}")
            st.caption(f"Tarih: {h_exam.created_at}")
            
            with st.expander("Soruları Göster", expanded=True):
                for i, q in enumerate(h_exam.questions, 1):
                     st.markdown(f"**{i}. {q.text}** ({q.difficulty})")
                     if q.q_type == "Multiple Choice" and q.options:
                        try:
                            opts = json.loads(q.options)
                            for opt in opts:
                                st.caption(f"- {opt}")
                        except:
                            pass

            # Export
            st.markdown("### 📥 İndir")
            
            # Generate in memory
            docx_data = export_to_docx(h_exam, filename=None)
            pdf_data = export_to_pdf(h_exam, filename=None)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="⬇️ Word Olarak İndir",
                    data=docx_data,
                    file_name=f"sinav_gecmis_{h_exam.id}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            with col2:
                 st.download_button(
                    label="⬇️ PDF Olarak İndir",
                    data=pdf_data,
                    file_name=f"sinav_gecmis_{h_exam.id}.pdf",
                    mime="application/pdf"
                )
