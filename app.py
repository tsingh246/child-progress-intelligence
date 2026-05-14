import streamlit as st
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_HOST=os.getenv("DB_HOST")
DB_PORT=os.getenv("DB_PORT")
DB_NAME=os.getenv("DB_NAME")
DB_USER=os.getenv("DB_USER")
DB_PASSWORD=os.getenv("DB_PASSWORD")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)


st.title("Child Progress Intelligence")

st.write("Local MVP is connected to PostgreSQL.")

entry_date = st.date_input("Report Date")

source_type = st.selectbox(
    "Source Type",
    ["aba", "parent", "speech", "ot"]
)

raw_text = st.text_area("Raw Report / Parent Note")


if st.button("Save Entry"):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO daily_entries (entry_date, source_type, raw_text)
                VALUES (:entry_date, :source_type, :raw_text)
            """),
            {
                "entry_date": entry_date,
                "source_type": source_type,
                "raw_text": raw_text
            }
        )
        conn.commit()

    st.success("Entry saved successfully.")


st.subheader("Saved Entries")

with engine.connect() as conn:
    result = conn.execute(
        text("""
            SELECT id, entry_date, source_type, raw_text, created_at
            FROM daily_entries
            ORDER BY created_at DESC
            LIMIT 10
        """)
    )

    rows = result.fetchall()

for row in rows:
    st.write(row)