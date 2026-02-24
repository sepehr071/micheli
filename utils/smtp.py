import os
import time
import logging
import dotenv
import ssl
from email.message import EmailMessage
import smtplib
from langchain_openai import ChatOpenAI
from config.services import SERVICES
from config.settings import SMTP_CONFIG, LLM_MODEL, LLM_TEMPERATURE, OPENROUTER_BASE_URL
from config.messages import EMAIL_TEMPLATES, EMAIL_SUMMARY_PROMPT, FALLBACK_NOT_PROVIDED
from config.messages.email import get_email_summary_prompt, get_email_templates
from config.language import language_manager

logger = logging.getLogger(__name__)


dotenv.load_dotenv()

email_sender = os.getenv("EMAIL_SENDER")
email_password = os.getenv("EMAIL_PASSWORD")

llm = ChatOpenAI(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
    openai_api_base=OPENROUTER_BASE_URL,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
)


def _send_via_smtp(em: EmailMessage, recipient: str, retries: int = 3) -> bool:
    """Send an email via SMTP with retry. Returns True on success."""
    context = ssl.create_default_context()
    for attempt in range(retries):
        try:
            with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"], timeout=SMTP_CONFIG["timeout"]) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, recipient, em.as_string())
            return True
        except Exception as e:
            logger.warning(f"SMTP attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))

    logger.error(f"SMTP send to {recipient} failed after {retries} attempts")
    return False


def send_email(recipient: str, formatted_date: str, formatted_time: str, products) -> bool:
    """Send appointment confirmation email to customer."""
    subject = EMAIL_TEMPLATES["appointment_subject"].format(
        date=formatted_date or "TBD", time=formatted_time or "TBD",
    )

    # Build products list with fallbacks for missing fields
    if products:
        products_list = '\n                '.join(
            f"  - {product.get('name', product.get('product_name', 'Unknown'))}"
            for product in products
        )
    else:
        products_list = EMAIL_TEMPLATES.get("no_products_selected", "No products selected")

    body = EMAIL_TEMPLATES["appointment_body"].format(
        date=formatted_date or "TBD", time=formatted_time or "TBD", products_list=products_list,
    )

    em = EmailMessage()
    em['subject'] = subject
    em['from'] = email_sender
    em['to'] = recipient
    em.set_content(body)

    return _send_via_smtp(em, recipient)


def send_email_summary(recipient: str, summary_context, language: str = None) -> bool:
    """
    Send a conversation summary email to the recipient.

    Args:
        recipient: Email address to send to
        summary_context: Context data for generating the summary (can be None)
        language: Language code for the summary (e.g., "en", "de", "tr").
                  If None, uses the current language from language_manager.
    """
    # Get the current language if not specified
    if language is None:
        language = language_manager.get_language()

    # Get language-specific prompts and templates
    summary_prompt_template = get_email_summary_prompt(language)
    templates = get_email_templates(language)

    # Handle None or empty summary_context
    if not summary_context:
        context_str = "No conversation details available."
    else:
        context_str = str(summary_context)

    summary = None
    summary_prompt = summary_prompt_template.format(context=context_str)
    for attempt in range(3):
        try:
            summary = llm.invoke(summary_prompt).content.strip()
            break
        except Exception as e:
            logger.warning(f"Summary LLM attempt {attempt + 1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(1 * (attempt + 1))

    if summary is None:
        logger.error("Summary LLM failed after 3 attempts, using raw context")
        summary = context_str[:2000]

    subject = templates["summary_subject"]
    body = templates["summary_body"].format(summary=summary)

    em = EmailMessage()
    em['subject'] = subject
    em['from'] = email_sender
    em['to'] = recipient
    em.set_content(body)

    return _send_via_smtp(em, recipient)


def send_lead_notification(
    company_email: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    schedule_date: str,
    schedule_time: str,
    reachability: str,
    purchase_timing: str,
    next_step: str,
    lead_degree: float,
    confidence: int,
    products: list
) -> bool:
    """Send lead notification to company when appointment is confirmed."""

    # Map internal keys to display labels from config
    timing_labels = SERVICES["purchase_timing"]
    step_labels = SERVICES["service_options"]
    reach_labels = SERVICES["reachability"]

    # Build products list with fallbacks
    if products:
        products_list = '\n'.join(
            f"  - {product.get('name', product.get('product_name', 'N/A'))}"
            for product in products
        )
    else:
        products_list = EMAIL_TEMPLATES.get("no_products_selected", "No products selected")

    subject = EMAIL_TEMPLATES["lead_subject"].format(
        name=customer_name,
        timing=timing_labels.get(purchase_timing, purchase_timing),
    )

    body = EMAIL_TEMPLATES["lead_body"].format(
        customer_name=customer_name,
        customer_phone=customer_phone or FALLBACK_NOT_PROVIDED,
        customer_email=customer_email or FALLBACK_NOT_PROVIDED,
        schedule_date=schedule_date,
        schedule_time=schedule_time,
        purchase_timing=timing_labels.get(purchase_timing, purchase_timing or FALLBACK_NOT_PROVIDED),
        next_step=step_labels.get(next_step, next_step or FALLBACK_NOT_PROVIDED),
        reachability=reach_labels.get(reachability, reachability or FALLBACK_NOT_PROVIDED),
        lead_degree=lead_degree,
        products_list=products_list,
    )

    em = EmailMessage()
    em['subject'] = subject
    em['from'] = email_sender
    em['to'] = company_email
    em.set_content(body)

    return _send_via_smtp(em, company_email)
