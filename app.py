import os
import json
import datetime
from collections import Counter

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
    ["aba", "parent", "speech", "ot", "bcba_weekly_note"]
)
session_period = st.selectbox(
    "Session Period",
    ["AM", "PM", "Full Day", "Parent/Home", "Weekly Review"]
)

therapist_name = st.text_input("Therapist Name")

default_text = st.session_state.get("ocr_text", "")

raw_text = st.text_area(
    "Raw Report / Parent Note",
    value=default_text,
    height=250
)

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

if raw_text:
    st.subheader("Preview Structured Extraction")
    preview_data = extract_structured_data(raw_text,engine)
    st.json(preview_data)

    if st.button("Save Entry"):
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
                    "structured_data": json.dumps(preview_data)
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
            ORDER BY entry_date DESC
            LIMIT 10
        """)
    )

    rows = result.fetchall()

for row in rows:
    with st.expander(f"{row.entry_date} - {row.source_type} ({row.session_period})"):
        st.write(f"**Therapist:** {row.therapist_name}")
        raw_preview = row.raw_text[:200] + "..." if len(row.raw_text) > 200 else row.raw_text
        st.write(f"**Raw Text:** {raw_preview}")
        st.write("**Structured Data:**")
        if row.structured_data:
            st.json(row.structured_data)
        else:
            st.write("None")


st.header("Weekly Insights")

with engine.connect() as conn:
    week_result = conn.execute(
        text(
            "SELECT DISTINCT date_trunc('week', entry_date)::date AS week_start "
            "FROM daily_entries "
            "ORDER BY week_start DESC"
        )
    )
    week_rows = week_result.fetchall()

week_options = [
    f"Week of {row.week_start.isoformat()}"
    for row in week_rows
]

if week_options:
    if (
        "selected_week" not in st.session_state
        or st.session_state.selected_week not in week_options
    ):
        st.session_state.selected_week = week_options[0]

    selected_week = st.selectbox(
        "Select week",
        week_options,
        key="selected_week"
    )
    selected_week_index = week_options.index(selected_week)
    selected_start = week_rows[selected_week_index].week_start
    selected_end = selected_start + datetime.timedelta(days=6)
    st.write(f"Insights for Week of {selected_start.isoformat()} ({selected_start.isoformat()} through {selected_end.isoformat()})")

    query = text(
        "SELECT structured_data FROM daily_entries "
        "WHERE entry_date >= :start_date AND entry_date <= :end_date"
    )
    params = {"start_date": selected_start, "end_date": selected_end}

    with engine.connect() as conn2:
        result = conn2.execute(query, params)
        rows = result.fetchall()

    if not rows:
        st.write("No entries this week")
    else:
        challenges = []
        positives = []
        for row in rows:
            data = row.structured_data
            if data:
                challenges.extend(data.get("challenges", []))
                positives.extend(data.get("positive_signals", []))

        if challenges:
            st.subheader("Top Challenges")
            counter = Counter(challenges)
            for item, count in counter.most_common(5):
                st.write(f"- {item} ({count} times)")

        if positives:
            st.subheader("Top Positive Signals")
            counter = Counter(positives)
            for item, count in counter.most_common(5):
                st.write(f"- {item} ({count} times)")
else:
    st.write("No entries this week")