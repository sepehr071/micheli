"""
Company configuration — identity, locale, contact info.
Edit this file to deploy the system for a new company.
All German text has English translations in comments.

Products → config/products.py
Services → config/services.py
"""

# =============================================================================
# COMPANY — identity, locale, contact
# =============================================================================

COMPANY = {
    "name": "Beauty Lounge Warendorf",                        # Short company name
    "full_name": "Beauty Lounge - Patrizia Miceli",           # Full legal/display name
    "description": "Kosmetikstudio & Beauty",                 # Company description
    "website": "beauty-lounge-warendorf.de",
    "language": "German",                                     # Response language
    "formality": "warm-professional",                         # Warm but formal (Sie) for B2C
    "timezone": "Europe/Berlin",
    "lead_emails": [                                          # Internal emails that receive lead notifications
        "info@beauty-lounge-warendorf.de",
    ],
    "email_closing": "Mit freundlichen Grüßen,\nIhr Beauty Lounge Team\nwww.beauty-lounge-warendorf.de",
    "greetings": {                                            # Time-of-day greetings
        "morning": "Guten Morgen!",                           # (05:00–11:59)
        "afternoon": "Guten Tag!",                            # (12:00–17:59)
        "evening": "Guten Abend!",                            # (18:00–21:59)
        "night": "Hallo!",                                    # (22:00–04:59)
    },
    "headquarters": "Warendorf, Nordrhein-Westfalen, Germany",
    "founded": "2005",
    "mission": "Ihnen ein gesundes und natürliches Aussehen zu verleihen — ganzheitliche Schönheit, Naturkosmetik und Nachhaltigkeit",
    # (To give you a healthy and natural appearance — holistic beauty, natural cosmetics and sustainability)
    "offices": {
        "warendorf": {
            "address": "Mühlenstraße 1, 48231 Warendorf, Germany",
            "phone": "+49 2581 787788",
            "mobile": "+49 172 6839430",
            "email": "info@beauty-lounge-warendorf.de",
        },
    },
    "social": {
        "instagram": "https://www.instagram.com/beauty.lounge.warendorf",
        "website": "https://beauty-lounge-warendorf.de",
    },
}
