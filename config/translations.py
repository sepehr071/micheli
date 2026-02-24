"""
Multi-language translations for trigger topics (buttons) and agent messages.

This module provides translations for:
- UI_BUTTONS (trigger topics sent to frontend)
- SERVICES (expert titles, service options, qualification choices)
- AGENT_MESSAGES (what agents say in various situations)
- QUALIFICATION_QUESTIONS
- And other text strings

Languages supported:
- English (en), German (de), Turkish (tr), Spanish (es), French (fr),
- Italian (it), Portuguese (pt), Dutch (nl), Polish (pl), Arabic (ar)
"""

from config.language import language_manager


# =============================================================================
# UI BUTTONS - Trigger topics sent to frontend
# =============================================================================

UI_BUTTONS_TRANSLATIONS = {
    "en": {
        "expert_offer": {"Yes": "Yes", "No": "No"},
        "appointment_confirm": {
            "Yes_please_send_me_an_appointment": "Yes",
            "No_please_dont_send_me_an_appointment": "No",
        },
        "summary_offer": {
            "Yes_please_give_me_the_summary": "Yes",
            "No_thank_you_I_dont_need_a_summary": "No",
        },
        "new_conversation": {
            "start_new_conversation": "start new conversation",
        },
    },
    "de": {
        "expert_offer": {"Ja": "Ja", "Nein": "Nein"},
        "appointment_confirm": {
            "Ja_bitte_sende_mir_einen_Termin": "Ja",
            "Nein_bitte_sende_mir_keinen_Termin": "Nein",
        },
        "summary_offer": {
            "Ja_bitte_gib_mir_die_Zusammenfassung": "Ja",
            "Nein_danke_ich_brauche_keine_Zusammenfassung": "Nein",
        },
        "new_conversation": {
            "neue_Konversation_beginnen": "neue Konversation beginnen",
        },
    },
    "tr": {
        "expert_offer": {"Evet": "Evet", "Hayır": "Hayır"},
        "appointment_confirm": {
            "Evet_lütfen_bana_randevu_gönder": "Evet",
            "Hayır_lütfen_bana_randevu_gönderme": "Hayır",
        },
        "summary_offer": {
            "Evet_lütfen_bana_özeti_ver": "Evet",
            "Hayır_teşekkürler_özet_ihtiyacım_yok": "Hayır",
        },
        "new_conversation": {
            "yeni_konuşma_başlat": "yeni konuşma başlat",
        },
    },
    "es": {
        "expert_offer": {"Sí": "Sí", "No": "No"},
        "appointment_confirm": {
            "Sí_por_favor_envíame_cita": "Sí",
            "No_por_favor_no_me_envíes_cita": "No",
        },
        "summary_offer": {
            "Sí_por_favor_dame_el_resumen": "Sí",
            "No_gracias_no_necesito_resumen": "No",
        },
        "new_conversation": {
            "iniciar_nueva_conversación": "iniciar nueva conversación",
        },
    },
    "fr": {
        "expert_offer": {"Oui": "Oui", "Non": "Non"},
        "appointment_confirm": {
            "Oui_sil_vous_plaît_envoyez_moi_un_rendez_vous": "Oui",
            "Non_sil_vous_plaît_ne_m_envoyez_pas_de_rendez_vous": "Non",
        },
        "summary_offer": {
            "Oui_sil_vous_plaît_donnez_moi_le_résumé": "Oui",
            "Non_merci_je_nai_pas_besoin_dun_résumé": "Non",
        },
        "new_conversation": {
            "commencer_nouvelle_conversation": "commencer nouvelle conversation",
        },
    },
    "it": {
        "expert_offer": {"Sì": "Sì", "No": "No"},
        "appointment_confirm": {
            "Sì_per_favore_inviami_un_appuntamento": "Sì",
            "No_per_favore_non_inviarmi_un_appuntamento": "No",
        },
        "summary_offer": {
            "Sì_per_favore_dammi_il_riepilogo": "Sì",
            "No_grazie_non_mi_serve_il_riepilogo": "No",
        },
        "new_conversation": {
            "inizia_nuova_conversazione": "inizia nuova conversazione",
        },
    },
    "pt": {
        "expert_offer": {"Sim": "Sim", "Não": "Não"},
        "appointment_confirm": {
            "Sim_por_favor_envie_me_um_compromisso": "Sim",
            "Não_por_favor_não_me_envie_compromisso": "Não",
        },
        "summary_offer": {
            "Sim_por_favor_dê_me_o_resumo": "Sim",
            "Não_obrigado_eu_não_preciso_de_resumo": "Não",
        },
        "new_conversation": {
            "iniciar_nova_conversa": "iniciar nova conversa",
        },
    },
    "nl": {
        "expert_offer": {"Ja": "Ja", "Nee": "Nee"},
        "appointment_confirm": {
            "Ja_stuur_mijn_alstublieft_een_afpraak": "Ja",
            "Nee_stuur_mijn_alstublieft_geen_afpraak": "Nee",
        },
        "summary_offer": {
            "Ja_geef_mijn_alstublieft_de_samenvatting": "Ja",
            "Nee_bedankt_ik_heb_geen_samenvatting_nodig": "Nee",
        },
        "new_conversation": {
            "start_nieuw_gesprek": "start nieuw gesprek",
        },
    },
    "pl": {
        "expert_offer": {"Tak": "Tak", "Nie": "Nie"},
        "appointment_confirm": {
            "Tak_proszę_wyślij_mi_umówienie": "Tak",
            "Nie_proszę_nie_wysyłaj_mi_umówienia": "Nie",
        },
        "summary_offer": {
            "Tak_proszę_daj_mi_podsumowanie": "Tak",
            "Nie_dziękuję_nie_potrzebuję_podsumowania": "Nie",
        },
        "new_conversation": {
            "rozpocznij_nową_konwersację": "rozpocznij nową konwersację",
        },
    },
    "ar": {
        "expert_offer": {"نعم": "نعم", "لا": "لا"},
        "appointment_confirm": {
            "نعم_يرجى_إرسال_موعد_لي": "نعم",
            "لا_يرجى_عدم_إرسال_موعد_لي": "لا",
        },
        "summary_offer": {
            "نعم_يرجى_إعطائي_الملخص": "نعم",
            "لا_شكرا_لا_أحتاج_ملخص": "لا",
        },
        "new_conversation": {
            "بدء_محادثة_جديدة": "بدء محادثة جديدة",
        },
    },
}


# =============================================================================
# SERVICES - Expert titles, service options, qualification choices
# =============================================================================

SERVICES_TRANSLATIONS = {
    "en": {
        "expert_title": "Beauty Consultant",
        "expert_title_alt": "Beauty Advisor",
        "primary_service": "Consultation",
        "off_topic_redirect": "That's not really my area – but I'd be happy to help you with {domain}!",
        "service_options": {
            "Schedule a consultation": "Schedule a consultation",
            "Discuss pricing and details": "Discuss pricing and details",
            "Continue exploring treatments": "Continue exploring treatments",
        },
        "purchase_timing": {
            "Right away or in the next few days": "Right away or in the next few days",
            "In 2 to 4 weeks": "In 2 to 4 weeks",
            "More like in a few months": "More like in a few months",
        },
        "reachability": {
            "By phone – today": "By phone – today",
            "Via WhatsApp – today": "Via WhatsApp – today",
            "By email – this week": "By email – this week",
        },
    },
    "de": {
        "expert_title": "Kosmetikerin",
        "expert_title_alt": "Beauty-Beraterin",
        "primary_service": "Beratungstermin",
        "off_topic_redirect": "Das ist leider nicht mein Bereich – aber bei {domain} kann ich Ihnen gerne weiterhelfen!",
        "service_options": {
            "Beratungstermin vereinbaren": "Beratungstermin vereinbaren",
            "Preise und Details besprechen": "Preise und Details besprechen",
            "Erstmal in Ruhe weiter umschauen": "Erstmal in Ruhe weiter umschauen",
        },
        "purchase_timing": {
            "Gleich oder in den nächsten Tagen": "Gleich oder in den nächsten Tagen",
            "In 2 bis 4 Wochen": "In 2 bis 4 Wochen",
            "Eher in ein paar Monaten": "Eher in ein paar Monaten",
        },
        "reachability": {
            "Am Telefon – am besten heute": "Am Telefon – am besten heute",
            "Per WhatsApp – heute": "Per WhatsApp – heute",
            "Per E-Mail – diese Woche": "Per E-Mail – diese Woche",
        },
    },
    "nl": {
        "expert_title": "Schoonheidsspecialist",
        "expert_title_alt": "Beauty Adviseur",
        "primary_service": "Consultatiegesprek",
        "off_topic_redirect": "Dat ligt niet echt binnen mijn expertise, maar met {domain} kan ik je zeker helpen!",
        "service_options": {
            "Een consultatiegesprek plannen": "Een consultatiegesprek plannen",
            "Prijs en details bespreken": "Prijs en details bespreken",
            "Ik kijk nog even rustig rond": "Ik kijk nog even rustig rond",
        },
        "purchase_timing": {
            "Nu of binnen een paar dagen": "Nu of binnen een paar dagen",
            "Over 2 tot 4 weken": "Over 2 tot 4 weken",
            "Eerder over een paar maanden": "Eerder over een paar maanden",
        },
        "reachability": {
            "Even bellen – vandaag": "Even bellen – vandaag",
            "Via WhatsApp – vandaag": "Via WhatsApp – vandaag",
            "Per e-mail – deze week": "Per e-mail – deze week",
        },
    },
    "fr": {
        "expert_title": "Esthéticienne",
        "expert_title_alt": "Conseillère Beauté",
        "primary_service": "Consultation",
        "off_topic_redirect": "Ce n'est pas vraiment mon domaine, mais pour {domain} je peux te donner un coup de main!",
        "service_options": {
            "Planifier une consultation": "Planifier une consultation",
            "Discuter du prix et des détails": "Discuter du prix et des détails",
            "Je continue à regarder un peu": "Je continue à regarder un peu",
        },
        "purchase_timing": {
            "Tout de suite ou dans les prochains jours": "Tout de suite ou dans les prochains jours",
            "Dans 2 à 4 semaines": "Dans 2 à 4 semaines",
            "Plutôt dans quelques mois": "Plutôt dans quelques mois",
        },
        "reachability": {
            "Par téléphone – aujourd'hui": "Par téléphone – aujourd'hui",
            "Par WhatsApp – aujourd'hui": "Par WhatsApp – aujourd'hui",
            "Par e-mail – cette semaine": "Par e-mail – cette semaine",
        },
    },
}


# =============================================================================
# AGENT MESSAGES - What agents say in various situations
# =============================================================================

AGENT_MESSAGES_TRANSLATIONS = {
    "en": {
        # contact_agents.py
        "ask_name": "only say: Could you tell me your full name?",
        "ask_phone": "(just ask the user and never greet) only say : What's the best phone number to reach you at?",
        "ask_email": "(just ask the user and never greet) only say : What email address should we use to get in touch?",
        "ask_email_and_phone": "(just ask the user and never greet) only say : Could you share your email and phone number so we can reach you?",
        "invalid_email": "only say: Hmm, that doesn't look like a valid email – mind trying again?",
        "schedule_call": """only say: Thank you very much! When would be the best time for a brief consultation call?""",
        "confirm_schedule": "Very Important: only say: Are you OK with us contacting you at this time?",

        # email_agents.py
        "email_thanks": "only say: Thanks so much for your interest! Someone from our team will be in touch. If you'd like, I can also email you a quick summary.",
        "offer_summary": "Very Important: only say: Want me to send you a quick recap of our chat?",
        "summary_sent": "only say: I've sent the summary to your email!",
        "email_error": "only say: Oops, something went wrong sending that email. Mind trying again in a bit?",
        "no_summary_thanks": "only say: Sounds good, thanks! Feel free to reach out anytime if you have more questions.",
        "ask_email_for_summary": "only say: What's your email address? I'll send over that summary.",

        # main_agent.py
        "expert_decline": "only say: No worries! Just let me know if you have any other questions.",
        "wait_for_customer": "Waiting for customer message before searching.",

        # resilience fallbacks
        "lead_email_failed": (
            "only say: Thanks so much! Unfortunately I ran into a small technical hiccup "
            "with forwarding your info. Best to give us a quick call or shoot us an email "
            "– that way nothing gets lost."
        ),
        "search_unavailable": (
            "TECHNICAL PROBLEM: Search is temporarily unavailable.\n"
            "INSTRUCTION: Friendly inform the customer that you're currently having "
            "technical difficulties with the search. Ask them to try again in a moment, "
            "or offer to connect them with a consultant."
        ),
        "patience_fallback": "Just a sec, I'll be right with you.",
    },
    "de": {
        # contact_agents.py
        "ask_name": "only say: Nennen Sie mir bitte Ihren vollständigen Namen",
        "ask_phone": "only say: Unter welcher Nummer können wir Sie am besten erreichen?",
        "ask_email": "only say: An welche E-Mail-Adresse dürfen wir Ihnen schreiben?",
        "ask_email_and_phone": "only say: Geben Sie mir bitte Ihre E-Mail-Adresse und Telefonnummer, damit wir Sie erreichen können.",
        "invalid_email": "only say: Das sieht nicht ganz nach einer gültigen E-Mail-Adresse aus – probieren Sie es bitte nochmal?",
        "schedule_call": """Only ask : for suitable date and time for the call""",
        "confirm_schedule": "Only ask this: Is it convenient for you that we contact you at this time?",

        # email_agents.py
        "email_thanks": "only say: Vielen Dank für Ihr Interesse! Einer aus unserem Team meldet sich bei Ihnen. Wenn Sie möchten, kann ich Ihnen auch gerne eine Zusammenfassung per Mail schicken.",
        "offer_summary": "only say: Soll ich Ihnen eine kurze Zusammenfassung von unserem Gespräch schicken?",
        "summary_sent": "only say: Ich habe Ihnen die Zusammenfassung per E-Mail geschickt!",
        "email_error": "only say: Hoppla, da gab's ein kleines Problem beim E-Mail-Versand. Probieren Sie es bitte später nochmal.",
        "no_summary_thanks": "only say: Alles klar, vielen Dank! Melden Sie sich gerne jederzeit wieder, wenn Sie weitere Fragen haben.",
        "ask_email_for_summary": "only say: Nennen Sie mir bitte Ihre E-Mail-Adresse, dann schicke ich Ihnen die Zusammenfassung zu.",

        # main_agent.py
        "expert_decline": "only say: Kein Problem! Melden Sie sich gerne, wenn Sie weitere Fragen haben.",
        "wait_for_customer": "Warte auf Kundennachricht bevor ich suche.",

        # resilience fallbacks
        "lead_email_failed": (
            "only say: Vielen Dank! Ich hatte leider ein kleines technisches Problem "
            "bei der Weiterleitung. Am besten rufen Sie kurz direkt bei uns an oder "
            "schreiben eine E-Mail – dann geht auf jeden Fall nichts verloren."
        ),
        "search_unavailable": (
            "TECHNISCHES PROBLEM: Die Suche ist gerade nicht verfügbar.\n"
            "ANWEISUNG: Sagen Sie der Kundin freundlich, dass Sie gerade technische "
            "Probleme mit der Suche haben. Bitten Sie sie, es in einem Moment "
            "nochmal zu versuchen, oder bieten Sie an, sie mit einer Beraterin zu verbinden."
        ),
        "patience_fallback": "Einen kleinen Moment bitte, ich bin gleich wieder da.",
    },
    "nl": {
        # contact_agents.py
        "ask_name": "only say: Vertel me alsjeblieft je volledige naam",
        "ask_phone": "only say: Op welk telefoonnummer kunnen we je bereiken?",
        "ask_email": "only say: Op welk e-mailadres mogen we je schrijven?",
        "ask_email_and_phone": "only say: Geef alsjeblieft je e-mailadres en telefoonnummer voor contact op.",
        "invalid_email": "only say: Geef alsjeblieft een geldig e-mailadres op.",
        "schedule_call": """only say: Hartelijk dank! Wanneer past een kort overleggesprek het beste?""",
        "confirm_schedule": "only say: Ben je akkoord dat we je op dit tijdstip bellen?",

        # email_agents.py
        "email_thanks": "only say: Hartelijk dank voor je interesse. Een teamlid zal je contacteren. Als je wilt, kan ik je een samenvatting per e-mail sturen.",
        "offer_summary": "only say: Wil je een samenvatting van ons gesprek?",
        "summary_sent": "only say: Een samenvatting is naar je e-mailadres gestuurd.",
        "email_error": "only say: Er was een probleem bij het versturen van de e-mail. Probeer het later alsjeblieft opnieuw.",
        "no_summary_thanks": "only say: Hartelijk dank. Neem gerust contact op als je meer vragen hebt.",
        "ask_email_for_summary": "only say: Geef me alsjeblieft je e-mailadres en ik stuur je de samenvatting.",

        # main_agent.py
        "expert_decline": "only say: Geen probleem! Laat me weten als je meer vragen hebt.",
        "wait_for_customer": "Wachten op klantbericht voordat ik zoek.",

        # resilience fallbacks
        "lead_email_failed": (
            "only say: Hartelijk dank! Ik had helaas een klein technisch probleem "
            "bij het doorsturen. Het is het beste om ons even direct te bellen of een e-mail te sturen "
            "— dan gaat er in ieder geval niets verloren."
        ),
        "search_unavailable": (
            "TECHNISCH PROBLEEM: Het zoeken is tijdelijk niet beschikbaar.\n"
            "INSTRUCTIE: Informeer de klant vriendelijk dat je momenteel technische "
            "moeilijkheden hebt met het zoeken. Vraag om het over een moment te proberen "
            "of bied aan om ze met een adviseur te verbinden."
        ),
        "patience_fallback": "Even geduld alsjeblieft, ik ben er zo weer voor je.",
    },
    "fr": {
        # contact_agents.py
        "ask_name": "only say: S'il vous plaît dites-moi votre nom complet",
        "ask_phone": "only say: À quel numéro de téléphone pouvons-nous vous joindre?",
        "ask_email": "only say: À quelle adresse e-mail devons-nous vous écrire?",
        "ask_email_and_phone": "only say: Pour le contact, veuillez fournir votre adresse e-mail et numéro de téléphone s'il vous plaît.",
        "invalid_email": "only say: Veuillez fournir une adresse e-mail valide.",
        "schedule_call": """only say: Merci beaucoup! Quand serait le meilleur moment pour un bref appel de consultation?""",
        "confirm_schedule": "only say: Êtes-vous d'accord pour que nous vous contactions à ce moment?",

        # email_agents.py
        "email_thanks": "only say: Merci beaucoup pour votre intérêt. Un membre de l'équipe vous contactera. Si vous le souhaitez, je peux vous envoyer un résumé par e-mail.",
        "offer_summary": "only say: Souhaitez-vous un résumé de notre conversation?",
        "summary_sent": "only say: Un résumé a été envoyé à votre adresse e-mail.",
        "email_error": "only say: Il y a eu un problème lors de l'envoi de l'e-mail. Veuillez réessayer plus tard.",
        "no_summary_thanks": "only say: Merci beaucoup. N'hésitez pas à nous contacter à tout moment si vous avez d'autres questions.",
        "ask_email_for_summary": "only say: Veuillez me donner votre adresse e-mail et je vous enverrai le résumé.",

        # main_agent.py
        "expert_decline": "only say: Pas de problème! Faites-moi savoir si vous avez d'autres questions.",
        "wait_for_customer": "En attente du message du client avant de chercher.",

        # resilience fallbacks
        "lead_email_failed": (
            "only say: Merci beaucoup! Malheureusement j'ai eu un petit problème technique "
            "avec le transfert. Il vaut mieux nous appeler directement brièvement ou envoyer un e-mail "
            "— comme ça rien ne sera perdu."
        ),
        "search_unavailable": (
            "PROBLÈME TECHNIQUE: La recherche est temporairement indisponible.\n"
            "INSTRUCTION: Informez poliment le client que vous avez actuellement des "
            "difficultés techniques avec la recherche. Demandez-lui de réessayer dans un moment "
            "ou proposez de le connecter avec un consultant."
        ),
        "patience_fallback": "Un instant s'il vous plaît, je suis immédiatement avec vous.",
    },
}


# =============================================================================
# QUALIFICATION QUESTIONS
# =============================================================================

QUALIFICATION_QUESTIONS_TRANSLATIONS = {
    "en": {
        "purchase_timing": "only say: When were you thinking of booking a treatment?",
        "next_step": "only say: What would you like to do next?",
        "reachability": "only say: What's the best way to reach you – and when works for you?",
    },
    "de": {
        "purchase_timing": "only say: Wann möchten Sie die Behandlung ungefähr buchen?",
        "next_step": "only say: Was möchten Sie als Nächstes gerne machen?",
        "reachability": "only say: Wie können wir Sie am besten erreichen – und wann passt es Ihnen?",
    },
    "nl": {
        "purchase_timing": "only say: Wanneer dacht je ongeveer de oplossing te implementeren?",
        "next_step": "only say: Wat wil je daarna doen?",
        "reachability": "only say: Hoe kunnen we je het beste bereiken – en wanneer schikt het?",
    },
    "fr": {
        "purchase_timing": "only say: Tu pensais mettre en œuvre la solution quand, environ?",
        "next_step": "only say: Qu'est-ce que tu voudrais faire ensuite?",
        "reachability": "only say: Comment on peut te joindre le mieux – et quand ça t'arrange?",
    },
}


# =============================================================================
# FALLBACK NOT PROVIDED
# =============================================================================

FALLBACK_NOT_PROVIDED_TRANSLATIONS = {
    "en": "Not provided",
    "de": "Nicht angegeben",
    "nl": "Niet opgegeven",
    "fr": "Non fourni",
}


# =============================================================================
# HELPER FUNCTIONS TO GET TRANSLATED CONTENT
# =============================================================================

def get_ui_buttons(button_type: str) -> dict:
    """
    Get UI buttons for current language.

    Args:
        button_type: Type of buttons (e.g., "expert_offer", "appointment_confirm")

    Returns:
        Dictionary of button labels and values in the current language
    """
    current_lang = language_manager.get_language()
    translations = UI_BUTTONS_TRANSLATIONS.get(current_lang, UI_BUTTONS_TRANSLATIONS["en"])
    return translations.get(button_type, {})


def get_services() -> dict:
    """
    Get services configuration for current language.

    Returns:
        Dictionary with expert_title, service_options, etc. in current language
    """
    current_lang = language_manager.get_language()
    translations = SERVICES_TRANSLATIONS.get(current_lang, SERVICES_TRANSLATIONS["en"])
    return translations


def get_agent_messages() -> dict:
    """
    Get agent messages for current language.

    Returns:
        Dictionary of agent message strings in current language
    """
    current_lang = language_manager.get_language()
    translations = AGENT_MESSAGES_TRANSLATIONS.get(current_lang, AGENT_MESSAGES_TRANSLATIONS["en"])
    return translations


def get_qualification_questions() -> dict:
    """
    Get qualification questions for current language.

    Returns:
        Dictionary of question strings in current language
    """
    current_lang = language_manager.get_language()
    translations = QUALIFICATION_QUESTIONS_TRANSLATIONS.get(current_lang, QUALIFICATION_QUESTIONS_TRANSLATIONS["en"])
    return translations


def get_fallback_not_provided() -> str:
    """
    Get fallback "not provided" text for current language.

    Returns:
        String to use when data is not provided
    """
    current_lang = language_manager.get_language()
    translations = FALLBACK_NOT_PROVIDED_TRANSLATIONS.get(current_lang, FALLBACK_NOT_PROVIDED_TRANSLATIONS["en"])
    return translations
