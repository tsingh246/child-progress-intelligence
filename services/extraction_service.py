from sqlalchemy import text


def extract_structured_data(raw_text, engine):

    text_lower = raw_text.lower()

    structured_data = {
        "challenges": [],
        "positive_signals": [],
        "communication": [],
        "contexts": [],
        "interventions": [],
        "parent_observations": []
    }

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

        category = rule.category
        normalized_value = rule.normalized_value
        keyword = rule.keyword.lower()

        if keyword in text_lower:

            if category in structured_data:

                if normalized_value not in structured_data[category]:
                    structured_data[category].append(normalized_value)

    return structured_data