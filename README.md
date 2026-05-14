# Child Progress Intelligence

## Overview

Child Progress Intelligence is a privacy-first local web application designed to help parents and therapists better understand a child’s development over time using therapy reports, parent observations, and contextual signals.

The goal of the project is not to replace therapists or clinical assessment.

Instead, the system aims to:

* Combine structured and unstructured observations
* Detect patterns over time
* Improve communication between home and therapy environments
* Generate weekly insights from daily therapy data
* Capture both challenges and positive developmental signals

---

# Core Philosophy

## Track connection, not perfection.

The project focuses on:

* Engagement
* Communication
* Context
* Progress over time

rather than isolated daily events or rigid assessment snapshots.

---

# Current MVP Scope

The current MVP supports:

* Local-only usage
* PostgreSQL local database
* Streamlit web UI
* OCR-based report ingestion
* Manual parent note entry
* Rule-based structured extraction
* Multiple image uploads
* Pluggable OCR architecture

---

# Architecture

```text
Image Upload
    ↓
OCR Provider
    ↓
Editable Raw Text
    ↓
Structured Extraction
    ↓
PostgreSQL Storage
    ↓
Weekly Insights (Upcoming)
```

---

# Current Tech Stack

| Layer              | Technology    |
| ------------------ | ------------- |
| UI                 | Streamlit     |
| Database           | PostgreSQL    |
| OCR                | Tesseract OCR |
| Language           | Python        |
| ORM/DB Access      | SQLAlchemy    |
| Environment Config | python-dotenv |
| Version Control    | Git + GitHub  |

---

# Current Features

## 1. Local Privacy-First App

* All data stored locally
* No cloud dependency
* No user accounts
* No external storage

---

## 2. OCR Report Processing

Supports:

* PNG
* JPG
* JPEG

Multiple images can be uploaded per entry.

---

## 3. Editable OCR Review

OCR output is shown to the user before saving.

This allows:

* correction of OCR mistakes
* validation of extracted text
* higher-quality downstream insights

---

## 4. Structured Extraction Engine

The app converts unstructured text into normalized categories.

Example:

```json
{
  "challenges": ["aggression"],
  "contexts": ["peer interaction"],
  "communication": ["AAC used or mentioned"]
}
```

---

## 5. Database-Driven Extraction Rules

Extraction keywords are stored in PostgreSQL instead of hardcoded Python.

This allows:

* incremental learning
* OCR variation handling
* easier tuning
* future admin UI support

---

# Database Schema (Current)

## Table: daily_entries

| Column          | Description                      |
| --------------- | -------------------------------- |
| id              | Primary key                      |
| entry_date      | Date of report                   |
| source_type     | aba / parent / speech / ot       |
| session_period  | AM / PM / Full Day / Parent/Home |
| therapist_name  | Therapist name                   |
| raw_text        | Original OCR/manual text         |
| structured_data | Extracted JSON data              |
| created_at      | Timestamp                        |

---

## Table: extraction_rules

| Column           | Description                      |
| ---------------- | -------------------------------- |
| category         | challenges / communication / etc |
| normalized_value | Standardized meaning             |
| keyword          | OCR or phrase match              |
| active           | Rule enabled/disabled            |

---

# Current Folder Structure

```text
child_progress_intelligence/
│
├── app.py
├── requirements.txt
├── .env
│
├── services/
│   ├── __init__.py
│   ├── extraction_service.py
│   │
│   └── ocr/
│       ├── __init__.py
│       ├── ocr_factory.py
│       ├── tesseract_ocr.py
│       └── image_preprocessing.py
```

---

# OCR Provider Architecture

The application supports pluggable OCR providers.

Current:

* Tesseract OCR

Planned:

* Ollama Vision Models
* OpenAI Vision
* Azure OCR
* Claude Vision

The OCR layer is isolated using a factory pattern.

---

# Future Roadmap

## Phase 1 — Core Local MVP

* OCR ingestion
* Parent notes
* Structured extraction
* Weekly summaries

---

## Phase 2 — Better Extraction

* OCR preprocessing improvements
* Fuzzy matching
* AI-assisted extraction
* Semantic normalization

---

## Phase 3 — Intelligence Layer

* Weekly trend analysis
* Pattern detection
* Cross-environment comparison
* Communication tracking
* Engagement scoring

---

## Phase 4 — AI Enhancement

* OCR cleanup via local LLM
* Vision-based document understanding
* Context-aware insight generation
* Semantic search using pgvector

---

## Phase 5 — Packaging

* Local installable desktop app
* Optional hosted version
* Mobile companion app

---

# Design Principles

## Flexible Inputs

Different therapy centers use different forms.

The system should:

* accept messy data
* normalize concepts
* avoid rigid schemas

---

## Optional Context Signals

Examples:

* screen time
* sleep
* illness
* environmental changes

These are optional observations, not mandatory fields.

---

## Weekly Insights > Daily Noise

The system focuses on:

* trends
* repeated patterns
* contextual relationships

rather than reacting to isolated daily events.

---

# Long-Term Vision

Build a personalized developmental intelligence system that helps:

* parents understand progress
* therapists identify patterns
* therapy/home environments align better
* children receive more context-aware support

without replacing clinical expertise.

---

# Project Status

Current Stage:

Early Local MVP Development

Implemented:

* Project setup
* Git integration
* PostgreSQL integration
* OCR processing
* Rule-based extraction
* Multi-file upload
* OCR provider abstraction

Upcoming:

* Weekly insight engine
* Better OCR preprocessing
* AI-assisted extraction
