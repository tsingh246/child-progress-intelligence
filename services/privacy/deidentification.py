import re


def add_placeholder(mapping, placeholder, value):
    clean_value = clean_identifier(value)
    if clean_value:
        mapping[placeholder] = clean_value


def clean_identifier(value):
    if not value:
        return ""

    clean_value = " ".join(value.strip().split())
    clean_value = re.sub(r"[^A-Za-z ]", "", clean_value).strip()

    if not clean_value:
        return ""

    words = clean_value.split()
    if len(words) > 3:
        return ""

    if any(word.lower() in ["note", "from", "drop", "dropoff", "breakfast"] for word in words):
        return ""

    return clean_value


def collect_placeholder_map(raw_texts, therapist_names):
    placeholder_map = {}

    for index, therapist_name in enumerate(therapist_names, start=1):
        add_placeholder(placeholder_map, f"[THERAPIST_{index}]", therapist_name)

    for raw_text in raw_texts:
        child_match = re.search(
            r"client\s+initials?\s*[:\-]?\s*([A-Za-z]{1,12}(?:\s+[A-Za-z]{1,12}){0,2})",
            raw_text or "",
            flags=re.IGNORECASE,
        )
        if child_match:
            add_placeholder(placeholder_map, "[CHILD]", child_match.group(1))
            break

    return placeholder_map


def deidentify_text(text, placeholder_map):
    deidentified_text = text

    for placeholder, original_value in placeholder_map.items():
        deidentified_text = re.sub(
            re.escape(original_value),
            placeholder,
            deidentified_text,
            flags=re.IGNORECASE,
        )

    deidentified_text = re.sub(
        r"https?://\S+",
        "[LINK]",
        deidentified_text,
    )

    return deidentified_text


def restore_placeholders(text, placeholder_map):
    restored_text = text

    for placeholder, original_value in placeholder_map.items():
        restored_text = restored_text.replace(placeholder, original_value)

    return restored_text
