# Child Progress Intelligence

## Overview

Child Progress Intelligence is a privacy-first local Streamlit app for helping parents review child therapy progress over time using parent notes, ABA daily reports, and optional future therapy notes.

The app is not a replacement for clinicians or clinical decision-making. Its goal is to help organize observations, surface patterns, and prepare parent-friendly discussion points for therapy teams.

## Core Philosophy

Track connection, not perfection.

The project focuses on:

* Engagement
* Communication
* Context
* Positive signals
* Challenges
* Progress over time

Weekly patterns are preferred over reacting to isolated daily events.

## Current MVP Scope

The current MVP supports:

* Local-only usage
* Local PostgreSQL database
* Streamlit web UI
* Parent note entry
* ABA, Speech, OT, and BCBA weekly note source types
* Soft parent-friendly Streamlit UI
* Lightweight banner image for the app header
* Tesseract OCR for uploaded report images
* Multiple image uploads for OCR-supported report types
* Editable raw text before saving
* Rule-based structured extraction
* Extraction rules stored in PostgreSQL
* Local observation search across saved notes and reports
* Search expansion using active extraction rules
* Basic weekly insight summaries
* Parent-friendly weekly interpretation from available entries
* Downloadable weekly summary report
* Entry archive and restore flow

Parent notes are the most important input. Report images and clinician notes are optional context.

## Current Flow

```text
Parent note or optional report text/images
    -> OCR, when images are uploaded
    -> Editable raw text
    -> Rule-based structured extraction
    -> PostgreSQL storage
    -> Local observation search
    -> Weekly insights
```

## Current Tech Stack

| Layer              | Technology    |
| ------------------ | ------------- |
| UI                 | Streamlit     |
| Database           | PostgreSQL    |
| OCR                | Tesseract OCR |
| Language           | Python        |
| DB Access          | SQLAlchemy    |
| Environment Config | python-dotenv |
| Version Control    | Git + GitHub  |

## Current Source Types

* `parent`
* `aba`
* `speech`
* `ot`
* `bcba_weekly_note`

## Current Session Periods

* `AM`
* `PM`
* `Full Day`
* `Parent/Home`
* `Weekly Review`

## Database Schema

### Table: `daily_entries`

| Column          | Description                                      |
| --------------- | ------------------------------------------------ |
| `id`            | Primary key                                      |
| `entry_date`    | Date of report or note                           |
| `source_type`   | Entry source, such as parent, ABA, Speech, or OT |
| `session_period`| AM, PM, Full Day, Parent/Home, or Weekly Review  |
| `therapist_name`| Optional therapist or clinician name             |
| `raw_text`      | Original OCR/manual text                         |
| `structured_data` | Extracted JSON data                           |
| `created_at`    | Timestamp                                        |
| `is_active`     | True for active entries, false for archived ones |
| `deleted_at`    | Archive timestamp                                |

### Table: `extraction_rules`

| Column             | Description                      |
| ------------------ | -------------------------------- |
| `category`         | challenges / communication / etc |
| `normalized_value` | Standardized meaning             |
| `keyword`          | OCR or phrase match              |
| `active`           | Rule enabled/disabled            |

## Current Folder Structure

```text
child_progress_app/
|-- app.py
|-- requirements.txt
|-- README.md
|-- assets/
|   `-- therapy-progress-banner.png
|-- .env
|-- services/
|   |-- extraction_service.py
|   `-- ocr/
|       |-- ocr_factory.py
|       `-- tesseract_ocr.py
```

## OCR Provider Architecture

The OCR layer uses a small factory function so additional OCR providers can be added later.

Current provider:

* `tesseract`

Potential future providers:

* Ollama vision
* OpenAI vision
* Azure OCR

Cloud OCR or LLM integrations should not be added until explicitly requested.

## AI Summary Direction

The app is being prepared for future AI summaries, but no AI summary provider is connected yet.

Before adding AI, the app should preserve:

* original OCR/manual raw text
* parent-reviewed edited text
* entry metadata such as date, source type, session period, and therapist
* structured extraction output
* weekly summaries based only on available data

Future AI summaries should be grounded in saved entries and should not replace the original source text.

## Search Direction

The current search feature is local keyword search, not vector search.

It searches active saved entries across:

* raw text
* source type
* session period
* therapist or clinician name
* structured extraction JSON

Search terms are also expanded using active `extraction_rules`. For example, a search like `peer aggression` can also match related rule values such as peer contexts or normalized aggression terms when those rules exist.

Future semantic search may use `pgvector`, but that is not implemented yet.

## Design Principles

* Parent note is the only required input for a date entry.
* ABA report images are optional.
* Speech and OT reports are optional.
* BCBA weekly notes are optional.
* Missing optional data should not block analysis.
* Insights should be generated from available data only.
* The app should track both positive signals and challenges.
* The app should support parent-friendly insights and BCBA discussion points.
* Data should stay local unless the project direction explicitly changes.

## Project Status

Current stage: early local MVP development.

Implemented:

* Project setup
* PostgreSQL integration
* Soft parent-friendly Streamlit UI
* Lightweight app banner image
* Tesseract OCR processing
* Rule-based extraction
* Multi-file image upload
* OCR provider abstraction
* Local observation search
* Search expansion from extraction rules
* Basic weekly summaries
* Parent-friendly weekly interpretation
* Downloadable weekly summary report
* BCBA weekly note source type
* Entry archive and restore controls

Likely next improvements:

* Parent-note-first entry flow polish
* More detailed weekly insight wording
* OCR preprocessing
* Structured AI-summary output design
* Database migration notes for schema changes
