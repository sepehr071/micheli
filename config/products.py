"""
Product configuration — what the company offers.
Edit this file to change treatment categories, methods, and typo corrections.
"""

# =============================================================================
# PRODUCTS — treatment domain, categories, methods, typo corrections
# =============================================================================

PRODUCTS = {
    "domain": "Kosmetik & Beauty-Behandlungen",               # The service domain
    "singular": "Behandlung",                                  # Single service noun (Treatment)
    "plural": "Behandlungen",                                  # Plural service noun (Treatments)
    "search_action": "Gesprächszusammenfassung",               # What the user does (conversation summary)
    "specialties": [                                           # Company's areas of expertise
        "Gesichtsbehandlungen",                                # Facial treatments
        "Körperbehandlungen",                                  # Body treatments
        "Permanent Make-Up",                                   # Permanent makeup
        "Fußpflege & Maniküre",                                # Foot care & manicure
        "Apparative Kosmetik (Forma)",                         # Device-based cosmetics
        "Massagen & Wellness",                                 # Massages & wellness
    ],
    "categories": [                                            # Service type classifications
        "Gesichtsbehandlungen",                                # Facial treatments
        "Körperbehandlungen",                                  # Body treatments
        "Permanent Make-Up",                                   # Permanent makeup
        "Fußpflege",                                           # Foot care
        "Maniküre",                                            # Manicure
        "Massagen",                                            # Massages
        "Apparative Kosmetik",                                 # Device-based cosmetics
    ],
    "product_lines": {
        "treatments": {
            "name": "Klassische Kosmetik",
            "description": "Gesichts- und Körperbehandlungen mit natürlicher Kosmetik",
            # (Facial and body treatments with natural cosmetics)
            "models": [
                "Gesichtsreinigung", "Anti-Aging-Behandlung", "Hydrations-Behandlung",
                "Körperpeeling", "Body Wrapping", "Fußpflege", "Maniküre",
            ],
        },
        "permanent_makeup": {
            "name": "Permanent Make-Up",
            "description": "Professionelles Permanent Make-Up für Augenbrauen, Lippen und Eyeliner",
            # (Professional permanent makeup for eyebrows, lips and eyeliner)
            "models": [
                "Augenbrauen", "Lippen", "Eyeliner",
            ],
        },
        "apparative": {
            "name": "Apparative Kosmetik",
            "description": "Forma Radiofrequenz-Technologie und Brigitte Kettner Methode",
            # (Forma radio frequency technology and Brigitte Kettner method)
            "models": [
                "Forma Radiofrequenz", "Brigitte Kettner Methode",
            ],
        },
        "wellness": {
            "name": "Wellness & Massage",
            "description": "Massagen, Entspannung und ganzheitliches Wohlbefinden",
            # (Massages, relaxation and holistic wellbeing)
            "models": [
                "Ganzkörpermassage", "Entspannungsmassage",
            ],
        },
    },
    "use_case_categories": [],                                 # Not applicable for B2C beauty studio
    "colors": [],                                              # Not applicable
    "domain_keywords": [                                       # Words that indicate service-related interest
        "kosmetik", "behandlung", "gesicht", "haut", "pflege", "peeling",
        "massage", "permanent", "makeup", "make-up", "maniküre", "pediküre",
        "fußpflege", "lifting", "anti-aging", "kollagen", "forma",
        "radiofrequenz", "brigitte kettner", "naturkosmetik", "wellness",
        "entspannung", "beauty", "schönheit", "hautpflege", "körper",
    ],
    "product_keywords": [                                      # Specific treatment/method names
        "forma", "brigitte kettner", "permanent make-up", "gesichtsbehandlung",
        "körperbehandlung", "fußpflege", "maniküre", "massage",
        "radiofrequenz", "anti-aging", "peeling",
    ],
    "typo_corrections": {                                      # Common misspellings → correct terms
        "permanet": "permanent",
        "permenent": "permanent",
        "pernanent": "permanent",
        "manikure": "maniküre",
        "manikuere": "maniküre",
        "pedikure": "pediküre",
        "pedikuere": "pediküre",
        "fusspflege": "fußpflege",
        "fuepflege": "fußpflege",
        "fuβpflege": "fußpflege",
        "masage": "massage",
        "massge": "massage",
        "masssage": "massage",
        "brigite": "brigitte",
        "brigitta": "brigitte",
        "kossmetik": "kosmetik",
        "kosmetk": "kosmetik",
        "kosmetick": "kosmetik",
        "gesichtsbehandung": "gesichtsbehandlung",
        "radiofrequnz": "radiofrequenz",
        "radiofrequens": "radiofrequenz",
    },
}
