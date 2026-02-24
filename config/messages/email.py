"""
Email templates — appointment confirmations, summary emails, lead notifications.
Multi-language support for all email content.
Used by: utils/smtp.py
"""

from config.company import COMPANY
from config.products import PRODUCTS

# =============================================================================
# EMAIL SUMMARY PROMPTS - Multi-language
# =============================================================================

EMAIL_SUMMARY_PROMPTS = {
    "en": """Summarize the following chat in ENGLISH – short, clear, and from the user's perspective.

Guidelines:
- Describe only WHAT was actually discussed in the conversation.
- No statements about what was NOT mentioned.
- Write 3–5 sentences as a short, understandable summary.
- Focus exclusively on the content of the conversation.
- Respond only with the summary, no heading or additional text.

Chat:
{context}
""",

    "de": """Fasse den folgenden Chat auf DEUTSCH zusammen – kurz, klar und aus der Perspektive des Nutzers.

Richtlinien:
- Beschreibe nur, WAS im Gespräch tatsächlich besprochen wurde.
- Keine Aussagen darüber, was NICHT erwähnt wurde.
- Schreibe 3–5 Sätze als kurze, verständliche Zusammenfassung.
- Fokus ausschließlich auf den Inhalten der Unterhaltung.
- Antworte nur mit der Zusammenfassung, ohne Überschrift oder Zusatztexte.

Chat:
{context}
""",

    "nl": """Vat het volgende chatgesprek samen in HET NEDERLANDS – kort, duidelijk en vanuit het perspectief van de gebruiker.

Richtlijnen:
- Beschrijf alleen WAT er daadwerkelijk is besproken in het gesprek.
- Geen uitspraken over wat NIET is genoemd.
- Schrijf 3–5 zinnen als een korte, begrijpelijke samenvatting.
- Focus uitsluitend op de inhoud van het gesprek.
- Reageer alleen met de samenvatting, zonder kop of extra tekst.

Chat:
{context}
""",

    "fr": """Résumez le chat suivant en FRANÇAIS – court, clair et du point de vue de l'utilisateur.

Directives:
- Décrivez uniquement CE qui a été réellement discuté dans la conversation.
- Pas de déclarations sur ce qui n'a PAS été mentionné.
- Écrivez 3–5 phrases comme un résumé court et compréhensible.
- Concentrez-vous exclusivement sur le contenu de la conversation.
- Répondez uniquement avec le résumé, sans titre ni texte supplémentaire.

Chat:
{context}
""",
}

# Default (English) for backwards compatibility
EMAIL_SUMMARY_PROMPT = EMAIL_SUMMARY_PROMPTS["en"]


# =============================================================================
# EMAIL TEMPLATES - Multi-language
# =============================================================================

EMAIL_TEMPLATES_TRANSLATIONS = {
    "en": {
        "appointment_subject": "Consultation Appointment - {date} at {time}",
        "appointment_body": f"""Hello,

                Thank you for your consultation request!

                APPOINTMENT DETAILS:
                Date: {{date}}
                Time: {{time}}

                The {PRODUCTS['plural']} discussed:
                {{products_list}}

                Your appointment has been successfully booked.

                If you cannot make the appointment, please let us know at least 24 hours in advance.

                If you have any questions, please don't hesitate to contact us.

                {COMPANY['email_closing']}""",

        "summary_subject": f"Summary of Your {PRODUCTS['search_action']}",
        "summary_body": f"""Hello,

            Thank you for your inquiry!

            **Summary:**
            {{summary}}

            If you have any further questions, please feel free to contact us.

            {COMPANY['email_closing']}""",

        "lead_subject": "New Lead: {name} - {timing}",
        "lead_body": f"""═══════════════════════════════════════════════════
                NEW LEAD - {COMPANY['full_name']}
═══════════════════════════════════════════════════

CONTACT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name:           {{customer_name}}
Phone:          {{customer_phone}}
Email:          {{customer_email}}

APPOINTMENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Date:           {{schedule_date}}
Time:           {{schedule_time}}

QUALIFICATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Preferred Treatment Timing: {{purchase_timing}}
Next Step:      {{next_step}}
Availability:   {{reachability}}

LEAD RATING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Lead Degree:    {{lead_degree}}/10

INTERESTED {PRODUCTS['plural'].upper()}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{products_list}}

═══════════════════════════════════════════════════
""",

        "no_products_selected": f"  No {PRODUCTS['plural']} selected",
        "product_line_format": "Product: {name} - Category: {category}",
    },

    "de": {
        "appointment_subject": "Beratungstermin - {date} um {time} Uhr",
        "appointment_body": f"""Guten Tag,

                vielen Dank für Ihre Terminanfrage!

                TERMINDETAILS:
                Datum: {{date}}
                Uhrzeit: {{time}} Uhr

                Die besprochenen {PRODUCTS['plural']}:
                {{products_list}}

                Ihr Termin wurde erfolgreich gebucht.

                Sollten Sie den Termin nicht wahrnehmen können, informieren Sie uns bitte mindestens 24 Stunden im Voraus.

                Bei Fragen stehen wir Ihnen gerne zur Verfügung.

                {COMPANY['email_closing']}""",

        "summary_subject": f"Zusammenfassung Ihrer {PRODUCTS['search_action']}",
        "summary_body": f"""Guten Tag,

            vielen Dank für Ihre Anfrage!

            **Zusammenfassung:**
            {{summary}}

            Sollten Sie weitere Fragen haben, kontaktieren Sie uns gerne.

            {COMPANY['email_closing']}""",

        "lead_subject": "Neuer Lead: {name} - {timing}",
        "lead_body": f"""═══════════════════════════════════════════════════
                NEUER LEAD - {COMPANY['full_name']}
═══════════════════════════════════════════════════

KONTAKTDATEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name:           {{customer_name}}
Telefon:        {{customer_phone}}
E-Mail:         {{customer_email}}

TERMIN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Datum:          {{schedule_date}}
Uhrzeit:        {{schedule_time}}

QUALIFICATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gew\u00fcnschter Behandlungszeitraum: {{purchase_timing}}
Nächster Schritt: {{next_step}}
Erreichbarkeit: {{reachability}}

LEAD BEWERTUNG:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Lead Degree:    {{lead_degree}}/10

INTERESSIERTE {PRODUCTS['plural'].upper()}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{products_list}}

═══════════════════════════════════════════════════
""",

        "no_products_selected": f"  Keine {PRODUCTS['plural']} ausgewählt",
        "product_line_format": "Produkt: {name} - Kategorie: {category}",
    },

    "nl": {
        "appointment_subject": "Overlegafspraak - {date} om {time}",
        "appointment_body": f"""Beste,

                Bedankt voor uw afspraakverzoek!

                AFSPRAAKGEGEVENS:
                Datum: {{date}}
                Tijd: {{time}}

                De besproken {PRODUCTS['plural']}:
                {{products_list}}

                Uw afspraak is succesvol geboekt.

                Als u de afspraak niet kunt nakomen, laat het ons dan minstens 24 uur van tevoren weten.

                Als u vragen heeft, aarzel dan niet om contact met ons op te nemen.

                {COMPANY['email_closing']}""",

        "summary_subject": f"Samenvatting van Uw {PRODUCTS['search_action']}",
        "summary_body": f"""Beste,

            Bedankt voor uw aanvraag!

            **Samenvatting:**
            {{summary}}

            Als u verdere vragen heeft, neem dan gerust contact met ons op.

            {COMPANY['email_closing']}""",

        "lead_subject": "Nieuwe Lead: {name} - {timing}",
        "lead_body": f"""═══════════════════════════════════════════════════
                NIEUWE LEAD - {COMPANY['full_name']}
═══════════════════════════════════════════════════

CONTACTGEGEVENS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Naam:           {{customer_name}}
Telefoon:       {{customer_phone}}
Email:          {{customer_email}}

AFSPRAAK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Datum:          {{schedule_date}}
Tijd:           {{schedule_time}}

KWALIFICATIE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gewenst behandelmoment: {{purchase_timing}}
Volgende Stap:  {{next_step}}
Bereikbaarheid: {{reachability}}

LEAD BEOORDELING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Lead Graad:     {{lead_degree}}/10

{PRODUCTS['plural'].upper()} VAN INTERESSE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{products_list}}

═══════════════════════════════════════════════════
""",

        "no_products_selected": f"  Geen {PRODUCTS['plural']} geselecteerd",
        "product_line_format": "Product: {name} - Categorie: {category}",
    },

    "fr": {
        "appointment_subject": "Rendez-vous Consultation - {date} à {time}",
        "appointment_body": f"""Bonjour,

                Merci pour votre demande de rendez-vous!

                DÉTAILS DU RENDEZ-VOUS:
                Date: {{date}}
                Heure: {{time}}

                Les {PRODUCTS['plural']} discutés:
                {{products_list}}

                Votre rendez-vous a été réservé avec succès.

                Si vous ne pouvez pas assister au rendez-vous, veuillez nous en informer au moins 24 heures à l'avance.

                Si vous avez des questions, n'hésitez pas à nous contacter.

                {COMPANY['email_closing']}""",

        "summary_subject": f"Résumé de Votre {PRODUCTS['search_action']}",
        "summary_body": f"""Bonjour,

            Merci pour votre demande!

            **Résumé:**
            {{summary}}

            Si vous avez d'autres questions, n'hésitez pas à nous contacter.

            {COMPANY['email_closing']}""",

        "lead_subject": "Nouveau Lead: {name} - {timing}",
        "lead_body": f"""═══════════════════════════════════════════════════
                NOUVEAU LEAD - {COMPANY['full_name']}
═══════════════════════════════════════════════════

COORDONNÉES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nom:            {{customer_name}}
Téléphone:      {{customer_phone}}
Email:          {{customer_email}}

RENDEZ-VOUS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Date:           {{schedule_date}}
Heure:          {{schedule_time}}

QUALIFICATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Timing de traitement souhaité: {{purchase_timing}}
Prochaine Étape: {{next_step}}
Disponibilité:  {{reachability}}

ÉVALUATION DU LEAD:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Degré du Lead:  {{lead_degree}}/10

{PRODUCTS['plural'].upper()} D'INTÉRÊT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{products_list}}

═══════════════════════════════════════════════════
""",

        "no_products_selected": f"  Aucun {PRODUCTS['singular']} sélectionné",
        "product_line_format": "Produit: {name} - Catégorie: {category}",
    },
}

# Default (English) for backwards compatibility
EMAIL_TEMPLATES = EMAIL_TEMPLATES_TRANSLATIONS["en"]

# Backward compatibility aliases
EMAIL_TEMPLATES["no_cars_selected"] = EMAIL_TEMPLATES.get("no_products_selected", f"No {PRODUCTS['plural']} selected")
EMAIL_TEMPLATES["car_line_format"] = EMAIL_TEMPLATES.get("product_line_format", "Product: {name}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_email_summary_prompt(language: str = "en") -> str:
    """Get the email summary prompt for the specified language."""
    return EMAIL_SUMMARY_PROMPTS.get(language, EMAIL_SUMMARY_PROMPTS["en"])


def get_email_templates(language: str = "en") -> dict:
    """Get the email templates for the specified language."""
    templates = EMAIL_TEMPLATES_TRANSLATIONS.get(language, EMAIL_TEMPLATES_TRANSLATIONS["en"])
    # Add backward compatibility aliases
    templates["no_cars_selected"] = templates.get("no_products_selected", f"No {PRODUCTS['plural']} selected")
    templates["car_line_format"] = templates.get("product_line_format", "Product: {name}")
    return templates
