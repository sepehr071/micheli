"""
Conversation history file format — labels and structure for saved transcripts.
Used by: utils/history.py
"""

HISTORY_FORMAT = {
    "header": "CONVERSATION HISTORY",
    "date_format": "%d.%m.%Y %H:%M:%S",
    "transcript_header": "--- Transcript ---",
    "user_label": "[USER]:",
    "agent_label": "[LENA]:",
    "search_line": "Search #{search_num} — {count} Behandlung(en) found",
    "product_line": "{i}. {name} — {category}",
    "contact_header": "--- Contact Info ---",
    "contact_labels": {
        "name": "Name:",
        "email": "Email:",
        "phone": "Phone:",
        "schedule": "Schedule:",
        "schedule_time_sep": " um ",
        "purchase_timing": "Gewünschter Behandlungszeitraum:",
        "next_step": "Next Step:",
        "reachability": "Reachability:",
    },
    "empty_value": "—",
}
