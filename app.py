import os
import json

import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from services.extraction_service import extract_structured_data
#from services.ocr_service import extract_text_from_image
from services.ocr.ocr_factory import extract_text_from_image


load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)




st.title("Child Progress Intelligence")

st.write("Local MVP connected to PostgreSQL.")


entry_date = st.date_input("Report Date")

source_type = st.selectbox(
    "Source Type",
    ["aba", "parent", "speech", "ot"]
)
session_period = st.selectbox(
    "Session Period",
    ["AM", "PM", "Full Day", "Parent/Home"]
)

therapist_name = st.text_input("Therapist Name")
ocr_provider = st.selectbox(
    "OCR Provider",
    [
        "tesseract",
        "ollama_vision",
        "openai_vision"
    ]
)

uploaded_files = st.file_uploader(
    "Upload ABA Report Images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

ocr_text = ""

if uploaded_files:

    for uploaded_file in uploaded_files:

        st.image(
            uploaded_file,
            caption=uploaded_file.name,
            use_container_width=True
        )

    if st.button("Extract Text from Images"):

        combined_text = ""

        for uploaded_file in uploaded_files:

            extracted_text = extract_text_from_image(
                uploaded_file,
                ocr_provider
            )

            combined_text += "\n\n"
            combined_text += extracted_text

        st.session_state["ocr_text"] = combined_text

#raw_text = st.text_area("Raw Report / Parent Note")
default_text = st.session_state.get("ocr_text", "")

raw_text = st.text_area(
    "Raw Report / Parent Note",
    value=default_text,
    height=250
)

if raw_text:
    st.subheader("Preview Structured Extraction")
    preview_data = extract_structured_data(raw_text,engine)
    st.json(preview_data)


if st.button("Save Entry"):
    structured_data = extract_structured_data(raw_text,engine)

    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO daily_entries (entry_date, source_type, session_period, therapist_name, raw_text, structured_data)
                VALUES (:entry_date, :source_type, :session_period, :therapist_name, :raw_text, CAST(:structured_data AS JSONB))
            """),
            {
                "entry_date": entry_date,
                "source_type": source_type,
		"session_period": session_period,
    		"therapist_name": therapist_name,
                "raw_text": raw_text,
                "structured_data": json.dumps(structured_data)
            }
        )
        conn.commit()

    st.success("Entry saved successfully.")


st.subheader("Saved Entries")

with engine.connect() as conn:
    result = conn.execute(
        text("""
            SELECT id, entry_date, source_type, session_period, therapist_name, raw_text, structured_data, created_at
            FROM daily_entries
            ORDER BY created_at DESC
            LIMIT 10
        """)
    )

    rows = result.fetchall()

for row in rows:
    st.write(row)