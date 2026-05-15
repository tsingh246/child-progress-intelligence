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


with st.sidebar:
    st.header("New Entry")

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

    if source_type in ["aba", "speech", "ot"]:
        default_text = st.session_state.get("ocr_text", "")
        raw_label = "Raw report text or OCR output"
    elif source_type == "bcba_weekly_note":
        default_text = ""
        raw_label = "BCBA weekly note text (optional if you upload a document or share a link)"
    else:
        default_text = st.session_state.get("ocr_text", "")
        raw_label = "Raw Report / Parent Note"

    raw_text = st.text_area(
        raw_label,
        value=default_text,
        height=250
    )

    document_link = ""
    weekly_note_file = None

    if source_type in ["aba", "speech", "ot"]:
        ocr_provider = st.selectbox(
            "OCR Provider",
            [
                "tesseract",
                "ollama_vision",
                "openai_vision"
            ]
        )

        uploaded_files = st.file_uploader(
            "Upload report images for OCR",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                st.image(
                    uploaded_file,
                    caption=uploaded_file.name,
                    use_container_width=True
                )

            combined_text = ""
            for uploaded_file in uploaded_files:
                extracted_text = extract_text_from_image(
                    uploaded_file,
                    ocr_provider
                )

                combined_text += "\n\n"
                combined_text += extracted_text

            st.session_state["ocr_text"] = combined_text
            st.success("Upload processed")

    elif source_type == "bcba_weekly_note":
        weekly_note_file = st.file_uploader(
            "Upload BCBA Weekly Note Document",
            type=["pdf", "docx", "doc", "txt", "png", "jpg", "jpeg"],
            accept_multiple_files=False,
            help="Upload the BCBA weekly note document for reference."
        )
        document_link = st.text_input(
            "Document Link",
            help="Optional URL to an uploaded BCBA note in drive or shared storage."
        )

        if weekly_note_file:
            st.write(f"Uploaded document: {weekly_note_file.name}")

    if raw_text or (source_type == "bcba_weekly_note" and (document_link or weekly_note_file)):
        st.subheader("Preview Structured Extraction")

        entry_text = raw_text
        if source_type == "bcba_weekly_note":
            source_note = []
            if document_link:
                source_note.append(f"Document link: {document_link}")
            if weekly_note_file:
                source_note.append(f"Uploaded file: {weekly_note_file.name}")

            if source_note:
                metadata_text = "\n".join(source_note)
                if entry_text:
                    entry_text = f"{entry_text}\n\n{metadata_text}"
                else:
                    entry_text = metadata_text

        preview_data = extract_structured_data(entry_text, engine)
        st.json(preview_data)

        if st.button("Save Entry"):
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO daily_entries (entry_date, source_type, session_period, therapist_name, raw_text, structured_data, is_active, deleted_at)
                        VALUES (:entry_date, :source_type, :session_period, :therapist_name, :raw_text, CAST(:structured_data AS JSONB), TRUE, NULL)
                    """),
                    {
                        "entry_date": entry_date,
                        "source_type": source_type,
                        "session_period": session_period,
                        "therapist_name": therapist_name,
                        "raw_text": entry_text,
                        "structured_data": json.dumps(preview_data)
                    }
                )
                conn.commit()

            st.success("Entry saved successfully.")

    st.markdown("---")
    st.subheader("Manage Entries")

    manage_status = st.selectbox(
        "Entry status",
        ["Active", "Archived"],
        key="manage_status"
    )
    manage_date = st.date_input(
        "Filter entries by date",
        value=datetime.date.today(),
        key="manage_date"
    )
    if st.button("Load entries", key="manage_load"):
        st.session_state.manage_entries_loaded = True

    if st.session_state.get("manage_entries_loaded"):
        status_value = True if manage_status == "Active" else False
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT id, entry_date, source_type, session_period, therapist_name "
                    "FROM daily_entries "
                    "WHERE is_active = :is_active "
                    "AND entry_date = :entry_date "
                    "ORDER BY entry_date DESC"
                ),
                {"is_active": status_value, "entry_date": manage_date}
            )
            rows = result.fetchall()

        if not rows:
            st.write("No entries found for that date.")
        else:
            action_label = "Archive" if status_value else "Restore"
            for row in rows:
                cols = st.columns([3, 1])
                cols[0].write(f"{row.entry_date} — {row.source_type} / {row.session_period}")
                if cols[1].button(action_label, key=f"manage_{action_label.lower()}_{row.id}"):
                    with engine.connect() as conn:
                        if status_value:
                            conn.execute(
                                text(
                                    "UPDATE daily_entries SET is_active = FALSE, deleted_at = :deleted_at WHERE id = :id"
                                ),
                                {
                                    "deleted_at": datetime.datetime.now(),
                                    "id": row.id,
                                }
                            )
                            st.success("Entry archived.")
                        else:
                            conn.execute(
                                text(
                                    "UPDATE daily_entries SET is_active = TRUE, deleted_at = NULL WHERE id = :id"
                                ),
                                {"id": row.id}
                            )
                            st.success("Entry restored.")
                        conn.commit()

st.header("Weekly Insights")

with engine.connect() as conn:
    week_result = conn.execute(
        text(
            "SELECT DISTINCT date_trunc('week', entry_date)::date AS week_start "
            "FROM daily_entries "
            "WHERE is_active = TRUE "
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
        "WHERE entry_date >= :start_date AND entry_date <= :end_date "
        "AND is_active = TRUE"
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
        communication = []
        contexts = []
        interventions = []
        parent_observations = []

        for row in rows:
            data = row.structured_data
            if data:
                challenges.extend(data.get("challenges", []))
                positives.extend(data.get("positive_signals", []))
                communication.extend(data.get("communication", []))
                contexts.extend(data.get("contexts", []))
                interventions.extend(data.get("interventions", []))
                parent_observations.extend(data.get("parent_observations", []))

        st.subheader("Weekly Summary")
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            if positives:
                st.write("**✓ Positive Signals**")
                counter = Counter(positives)
                for item, count in counter.most_common(5):
                    st.write(f"- {item} ({count}x)")
            else:
                st.write("**✓ Positive Signals**\n*None recorded*")

            if communication:
                st.write("**💬 Communication**")
                counter = Counter(communication)
                for item, count in counter.most_common(5):
                    st.write(f"- {item} ({count}x)")

            if interventions:
                st.write("**🎯 Interventions Used**")
                counter = Counter(interventions)
                for item, count in counter.most_common(5):
                    st.write(f"- {item} ({count}x)")

        with col2:
            if challenges:
                st.write("**⚠ Challenges**")
                counter = Counter(challenges)
                for item, count in counter.most_common(5):
                    st.write(f"- {item} ({count}x)")
            else:
                st.write("**⚠ Challenges**\n*None recorded*")

            if contexts:
                st.write("**📍 Context**")
                counter = Counter(contexts)
                for item, count in counter.most_common(5):
                    st.write(f"- {item} ({count}x)")

            if parent_observations:
                st.write("**👥 Parent Observations**")
                counter = Counter(parent_observations)
                for item, count in counter.most_common(5):
                    st.write(f"- {item} ({count}x)")

        st.markdown("---")
        st.subheader("BCBA Discussion Points")
        total_entries = len(rows)
        st.write(f"**Week summary:** {total_entries} entries recorded")

        if challenges and positives:
            st.write(f"- Observed {len(set(challenges))} unique challenges and {len(set(positives))} positive signals")
        if communication:
            st.write(f"- Communication noted in {len(set(communication))} unique ways")
        if interventions:
            st.write(f"- {len(set(interventions))} different interventions observed or applied")

        st.write("→ *Bring this summary to your next BCBA meeting for detailed discussion*")
else:
    st.write("No entries this week")