import os
import json
import datetime
import re
from collections import Counter

import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from services.extraction_service import extract_structured_data
from services.ocr.ocr_factory import extract_text_from_image


load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)


st.set_page_config(
    page_title="Child Progress Intelligence",
    layout="wide"
)


def apply_soft_theme():
    st.markdown(
        """
        <style>
            :root {
                --cpi-bg: #f6f8f5;
                --cpi-panel: #ffffff;
                --cpi-panel-soft: #eef5f2;
                --cpi-text: #24302f;
                --cpi-muted: #64716f;
                --cpi-sage: #6f8f72;
                --cpi-blue: #6b8fb3;
                --cpi-coral: #d68b7c;
                --cpi-border: #dce5df;
            }

            .stApp {
                background:
                    linear-gradient(180deg, #f6f8f5 0%, #f9fbfa 44%, #f5f7fb 100%);
                color: var(--cpi-text);
            }

            [data-testid="stSidebar"] {
                background: #edf4f0;
                border-right: 1px solid var(--cpi-border);
            }

            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3 {
                color: #29443d;
            }

            h1, h2, h3 {
                color: #24302f;
                letter-spacing: 0;
            }

            h1 {
                font-weight: 760;
                margin-bottom: 0.2rem;
            }

            h2 {
                border-top: 1px solid var(--cpi-border);
                padding-top: 1.25rem;
            }

            div[data-testid="stMarkdownContainer"] p,
            div[data-testid="stMarkdownContainer"] li {
                color: var(--cpi-text);
            }

            .cpi-hero {
                background: rgba(255, 255, 255, 0.76);
                border: 1px solid var(--cpi-border);
                border-radius: 8px;
                padding: 1.1rem 1.25rem;
                margin: 0 0 1.25rem 0;
            }

            [data-testid="stImage"] img {
                border: 1px solid var(--cpi-border);
                border-radius: 8px;
                margin: 0.35rem 0 1rem 0;
            }

            .cpi-hero-title {
                font-size: 1.05rem;
                font-weight: 700;
                color: #29443d;
                margin-bottom: 0.25rem;
            }

            .cpi-hero-text {
                color: var(--cpi-muted);
                margin: 0;
            }

            div[data-testid="stExpander"] {
                background: rgba(255, 255, 255, 0.78);
                border: 1px solid var(--cpi-border);
                border-radius: 8px;
            }

            div[data-testid="stTextInput"] input,
            div[data-testid="stTextArea"] textarea,
            div[data-testid="stDateInput"] input,
            div[data-baseweb="select"] > div {
                border-radius: 8px;
                border-color: var(--cpi-border);
                background-color: #ffffff;
            }

            div.stButton > button,
            div.stDownloadButton > button {
                border-radius: 8px;
                border: 1px solid #bfd1c7;
                background: #e7f1ec;
                color: #29443d;
                font-weight: 650;
            }

            div.stButton > button:hover,
            div.stDownloadButton > button:hover {
                border-color: var(--cpi-sage);
                background: #dcebe4;
                color: #1f3832;
            }

            div[data-testid="stAlert"] {
                border-radius: 8px;
            }

            [data-testid="stJson"] {
                border-radius: 8px;
                border: 1px solid var(--cpi-border);
            }
        </style>
        """,
        unsafe_allow_html=True
    )


def format_list(items, max_items=3):
    if not items:
        return ""

    unique_items = []
    for item in items:
        if item not in unique_items:
            unique_items.append(item)

    return ", ".join(unique_items[:max_items])


def write_count_list(title, items):
    st.write(f"**{title}**")

    if not items:
        st.write("*None extracted yet*")
        return

    counter = Counter(items)
    for item, count in counter.most_common(5):
        st.write(f"- {item} ({count}x)")


def format_count_lines(items):
    if not items:
        return ["- None extracted yet"]

    counter = Counter(items)
    return [
        f"- {item} ({count}x)"
        for item, count in counter.most_common(5)
    ]


def as_dict(value):
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}

    return {}


def get_search_terms(search_text, engine):
    base_terms = [
        term.strip().lower()
        for term in re.split(r"[\s,]+", search_text)
        if term.strip()
    ]
    expanded_terms = list(base_terms)

    if not base_terms:
        return []

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT category, normalized_value, keyword
                FROM extraction_rules
                WHERE active = TRUE
            """)
        )
        rules = result.fetchall()

    for rule in rules:
        rule_values = [
            rule.category or "",
            rule.normalized_value or "",
            rule.keyword or ""
        ]
        rule_text = " ".join(rule_values).lower()

        if any(term in rule_text for term in base_terms):
            for value in rule_values:
                clean_value = value.strip().lower()
                if clean_value and clean_value not in expanded_terms:
                    expanded_terms.append(clean_value)

    return expanded_terms


def get_matching_terms(searchable_text, search_terms):
    text_lower = searchable_text.lower()
    return [
        term
        for term in search_terms
        if term in text_lower
    ]


def get_raw_text_preview(raw_text, search_terms, preview_length=260):
    if not raw_text:
        return ""

    raw_text_single_line = " ".join(raw_text.split())
    raw_text_lower = raw_text_single_line.lower()

    first_match_index = -1
    for term in search_terms:
        term_index = raw_text_lower.find(term)
        if term_index != -1 and (first_match_index == -1 or term_index < first_match_index):
            first_match_index = term_index

    if first_match_index == -1:
        return raw_text_single_line[:preview_length]

    start_index = max(first_match_index - 80, 0)
    end_index = start_index + preview_length
    prefix = "... " if start_index > 0 else ""
    suffix = " ..." if end_index < len(raw_text_single_line) else ""

    return f"{prefix}{raw_text_single_line[start_index:end_index]}{suffix}"


def write_weekly_interpretation(
    total_entries,
    source_counts,
    positives,
    challenges,
    communication,
    contexts,
    interventions,
    parent_observations
):
    source_summary = ", ".join(
        f"{source_type}: {count}"
        for source_type, count in source_counts.items()
    )

    st.subheader("Parent-Friendly Interpretation")
    st.write(
        f"This week includes {total_entries} saved entries"
        f" from the available sources ({source_summary})."
    )

    if positives:
        st.write(
            "Positive signs were noted, including "
            f"{format_list(positives)}."
        )
    else:
        st.write("No positive signals were extracted yet from the saved entries.")

    if challenges:
        challenge_text = format_list(challenges)
        if contexts:
            st.write(
                f"Challenges included {challenge_text}. "
                f"Reported contexts included {format_list(contexts)}."
            )
        else:
            st.write(f"Challenges included {challenge_text}.")
    else:
        st.write("No challenges were extracted yet from the saved entries.")

    if communication:
        st.write(
            "Communication-related notes included "
            f"{format_list(communication)}."
        )

    if interventions:
        st.write(
            "Interventions or supports mentioned this week included "
            f"{format_list(interventions)}."
        )

    if parent_observations:
        st.write(
            "Parent observations added extra home context, including "
            f"{format_list(parent_observations)}."
        )

    st.write(
        "This summary uses only the information entered so far. "
        "Missing reports or notes do not block the weekly review."
    )


def write_bcba_discussion_points(
    total_entries,
    positives,
    challenges,
    communication,
    contexts,
    interventions
):
    st.subheader("BCBA Discussion Points")
    st.write(f"**Week summary:** {total_entries} entries recorded")

    if challenges and contexts:
        st.write(
            f"- Ask about patterns connecting {format_list(challenges)} "
            f"with contexts such as {format_list(contexts)}."
        )
    elif challenges:
        st.write(f"- Ask about support strategies for {format_list(challenges)}.")

    if communication:
        st.write(
            f"- Discuss communication supports noted this week, including "
            f"{format_list(communication)}."
        )

    if interventions:
        st.write(
            f"- Review whether supports such as {format_list(interventions)} "
            "are helping across settings."
        )

    if positives:
        st.write(
            f"- Highlight positive signs such as {format_list(positives)} "
            "and ask how to build on them."
        )

    if not any([positives, challenges, communication, contexts, interventions]):
        st.write("- Add more parent notes or reports to generate discussion points.")

    st.write("*Bring this summary to your next BCBA meeting for detailed discussion.*")


def build_weekly_report_text(
    selected_start,
    selected_end,
    total_entries,
    source_counts,
    session_counts,
    therapist_names,
    positives,
    challenges,
    communication,
    contexts,
    interventions,
    parent_observations
):
    source_summary = ", ".join(
        f"{source_type}: {count}"
        for source_type, count in source_counts.items()
    )
    session_summary = ", ".join(
        f"{session_period}: {count}"
        for session_period, count in session_counts.items()
    )
    therapist_summary = format_list(therapist_names, 8) or "None listed"

    lines = [
        "Child Progress Intelligence - Weekly Summary Report",
        f"Week: {selected_start.isoformat()} through {selected_end.isoformat()}",
        "",
        "Available Inputs",
        f"- Entries included: {total_entries}",
        f"- Sources: {source_summary or 'None'}",
        f"- Session periods: {session_summary or 'None'}",
        f"- Therapists / clinicians mentioned: {therapist_summary}",
        "",
        "Positive Signs",
        *format_count_lines(positives),
        "",
        "Challenges",
        *format_count_lines(challenges),
        "",
        "Contexts / Triggers",
        *format_count_lines(contexts),
        "",
        "Communication",
        *format_count_lines(communication),
        "",
        "Interventions / Supports",
        *format_count_lines(interventions),
        "",
        "Parent Observations",
        *format_count_lines(parent_observations),
        "",
        "Parent-Friendly Interpretation",
    ]

    if positives:
        lines.append(f"- Positive signs were noted, including {format_list(positives)}.")
    else:
        lines.append("- No positive signals were extracted yet from the saved entries.")

    if challenges and contexts:
        lines.append(
            f"- Challenges included {format_list(challenges)}. "
            f"Reported contexts included {format_list(contexts)}."
        )
    elif challenges:
        lines.append(f"- Challenges included {format_list(challenges)}.")
    else:
        lines.append("- No challenges were extracted yet from the saved entries.")

    if communication:
        lines.append(f"- Communication-related notes included {format_list(communication)}.")

    if interventions:
        lines.append(
            f"- Interventions or supports mentioned this week included "
            f"{format_list(interventions)}."
        )

    if parent_observations:
        lines.append(
            f"- Parent observations added extra home context, including "
            f"{format_list(parent_observations)}."
        )

    lines.extend([
        "",
        "BCBA Discussion Points",
    ])

    if challenges and contexts:
        lines.append(
            f"- Ask about patterns connecting {format_list(challenges)} "
            f"with contexts such as {format_list(contexts)}."
        )
    elif challenges:
        lines.append(f"- Ask about support strategies for {format_list(challenges)}.")

    if communication:
        lines.append(
            f"- Discuss communication supports noted this week, including "
            f"{format_list(communication)}."
        )

    if interventions:
        lines.append(
            f"- Review whether supports such as {format_list(interventions)} "
            "are helping across settings."
        )

    if positives:
        lines.append(
            f"- Highlight positive signs such as {format_list(positives)} "
            "and ask how to build on them."
        )

    if not any([positives, challenges, communication, contexts, interventions]):
        lines.append("- Add more parent notes or reports to generate discussion points.")

    lines.extend([
        "",
        "Note",
        "This report uses only the information entered so far. Missing optional reports or notes do not block the weekly review.",
        "This app does not replace clinicians or make clinical decisions.",
    ])

    return "\n".join(lines)




apply_soft_theme()

st.title("Child Progress Intelligence")

st.markdown(
    """
    <div class="cpi-hero">
        <div class="cpi-hero-title">Local therapy progress review for parents</div>
        <p class="cpi-hero-text">
            Enter parent notes, optional therapy reports, and weekly context.
            The app keeps data local and summarizes only what has been saved.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

banner_path = "assets/therapy-progress-banner.png"
if os.path.exists(banner_path):
    st.image(banner_path, use_container_width=True)


with st.sidebar:
    st.header("New Entry")

    entry_date = st.date_input("Report Date")

    source_type = st.selectbox(
        "Source Type",
        ["parent", "aba", "speech", "ot", "bcba_weekly_note"]
    )

    default_session_index = 3
    if source_type == "bcba_weekly_note":
        default_session_index = 4

    session_period = st.selectbox(
        "Session Period",
        ["AM", "PM", "Full Day", "Parent/Home", "Weekly Review"],
        index=default_session_index
    )

    therapist_name = st.text_input("Therapist Name (optional)")

    if source_type in ["aba", "speech", "ot"]:
        default_text = st.session_state.get("ocr_text", "")
        raw_label = "Raw report text or OCR output"
    elif source_type == "bcba_weekly_note":
        default_text = ""
        raw_label = "BCBA weekly note text (optional if you upload a document or share a link)"
    else:
        default_text = ""
        raw_label = "Parent note"

    raw_text = st.text_area(
        raw_label,
        value=default_text,
        height=250
    )

    document_link = ""
    weekly_note_file = None

    if source_type in ["aba", "speech", "ot"]:
        ocr_provider = "tesseract"
        st.caption("OCR provider: local Tesseract")

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
                cols[0].write(f"{row.entry_date} - {row.source_type} / {row.session_period}")
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

st.header("Search Observations")

search_text = st.text_input(
    "Search saved notes and reports",
    placeholder="Example: peer aggression"
)

search_col1, search_col2, search_col3 = st.columns(3)
with search_col1:
    search_start_date = st.date_input(
        "Search start date",
        value=datetime.date.today() - datetime.timedelta(days=90),
        key="search_start_date"
    )
with search_col2:
    search_end_date = st.date_input(
        "Search end date",
        value=datetime.date.today(),
        key="search_end_date"
    )
with search_col3:
    search_source_type = st.selectbox(
        "Search source",
        ["All", "parent", "aba", "speech", "ot", "bcba_weekly_note"],
        key="search_source_type"
    )

if search_text:
    search_terms = get_search_terms(search_text, engine)
    st.caption(f"Search terms used: {', '.join(search_terms)}")

    search_query = (
        "SELECT id, entry_date, source_type, session_period, therapist_name, raw_text, structured_data "
        "FROM daily_entries "
        "WHERE is_active = TRUE "
        "AND entry_date >= :start_date "
        "AND entry_date <= :end_date "
    )
    search_params = {
        "start_date": search_start_date,
        "end_date": search_end_date
    }

    if search_source_type != "All":
        search_query += "AND source_type = :source_type "
        search_params["source_type"] = search_source_type

    search_query += "ORDER BY entry_date DESC, id DESC"

    with engine.connect() as conn:
        search_result = conn.execute(text(search_query), search_params)
        possible_rows = search_result.fetchall()

    matching_rows = []
    matching_terms_by_entry = {}
    for row in possible_rows:
        structured_data = as_dict(row.structured_data)
        searchable_text = " ".join([
            row.raw_text or "",
            row.source_type or "",
            row.session_period or "",
            row.therapist_name or "",
            json.dumps(structured_data)
        ])

        matching_terms = get_matching_terms(searchable_text, search_terms)
        if matching_terms:
            matching_rows.append(row)
            matching_terms_by_entry[row.id] = matching_terms

    if not matching_rows:
        st.write("No matching observations found.")
    else:
        st.write(f"Found {len(matching_rows)} matching entries.")

        week_counts = Counter()
        for row in matching_rows:
            week_start = row.entry_date - datetime.timedelta(days=row.entry_date.weekday())
            week_counts[week_start] += 1

        st.write("**Matching Weeks**")
        for week_start, count in week_counts.most_common():
            week_end = week_start + datetime.timedelta(days=6)
            st.write(f"- {week_start.isoformat()} through {week_end.isoformat()} ({count} entries)")

        st.write("**Matching Entries**")
        for row in matching_rows:
            week_start = row.entry_date - datetime.timedelta(days=row.entry_date.weekday())
            title_parts = [
                str(row.entry_date),
                f"week of {week_start.isoformat()}",
                row.source_type,
                row.session_period
            ]
            if row.therapist_name:
                title_parts.append(row.therapist_name)

            with st.expander(" - ".join(title_parts)):
                structured_data = as_dict(row.structured_data)
                st.write(f"**Matched Terms:** {format_list(matching_terms_by_entry[row.id], 8)}")

                st.write("**Extracted Fields**")
                st.json(structured_data)

                st.write("**Raw Text Preview**")
                st.write(get_raw_text_preview(row.raw_text or "", search_terms))

                st.write("**Full Raw Text**")
                st.text_area(
                    "Matching entry raw text",
                    value=row.raw_text or "",
                    height=180,
                    key=f"search_raw_text_{row.id}",
                    disabled=True
                )

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
        "SELECT source_type, session_period, therapist_name, structured_data FROM daily_entries "
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
        source_counts = Counter()
        session_counts = Counter()
        therapist_names = []

        for row in rows:
            source_counts[row.source_type] += 1
            session_counts[row.session_period] += 1
            if row.therapist_name and row.therapist_name not in therapist_names:
                therapist_names.append(row.therapist_name)
            data = as_dict(row.structured_data)
            if data:
                challenges.extend(data.get("challenges", []))
                positives.extend(data.get("positive_signals", []))
                communication.extend(data.get("communication", []))
                contexts.extend(data.get("contexts", []))
                interventions.extend(data.get("interventions", []))
                parent_observations.extend(data.get("parent_observations", []))

        total_entries = len(rows)

        st.subheader("Available Inputs")
        st.write(f"**Entries included:** {total_entries}")
        write_count_list("Sources", list(source_counts.elements()))
        write_count_list("Session Periods", list(session_counts.elements()))

        if therapist_names:
            st.write(f"**Therapists / Clinicians Mentioned:** {format_list(therapist_names, 8)}")

        st.markdown("---")
        st.subheader("Extracted Weekly Signals")

        col1, col2 = st.columns(2)

        with col1:
            write_count_list("Positive Signs", positives)
            write_count_list("Communication", communication)
            write_count_list("Interventions / Supports", interventions)

        with col2:
            write_count_list("Challenges", challenges)
            write_count_list("Contexts / Triggers", contexts)
            write_count_list("Parent Observations", parent_observations)

        st.markdown("---")
        write_weekly_interpretation(
            total_entries,
            source_counts,
            positives,
            challenges,
            communication,
            contexts,
            interventions,
            parent_observations
        )

        st.markdown("---")
        write_bcba_discussion_points(
            total_entries,
            positives,
            challenges,
            communication,
            contexts,
            interventions
        )

        st.markdown("---")
        report_text = build_weekly_report_text(
            selected_start,
            selected_end,
            total_entries,
            source_counts,
            session_counts,
            therapist_names,
            positives,
            challenges,
            communication,
            contexts,
            interventions,
            parent_observations
        )
        st.download_button(
            "Download summary report",
            data=report_text,
            file_name=f"weekly_summary_{selected_start.isoformat()}.txt",
            mime="text/plain"
        )
else:
    st.write("No entries this week")
