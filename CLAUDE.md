# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LiveKit-based Python voice AI assistant for **Beauty Lounge Warendorf** (Kosmetikstudio & Beauty). The agent "Lena" assists with treatment consultations for facial treatments, permanent makeup, wellness/massage, and apparative cosmetics. Supports 10 languages with runtime switching.

> **Note:** The README.md is outdated and references a previous project ("Herbrand Berta" car dealership). The actual codebase serves Beauty Lounge Warendorf (Patrizia Miceli).

## Commands

### Install dependencies
```bash
pip install -r req.txt
```

### Run the agent
```bash
python agent.py
```
This starts a LiveKit worker via `agents.cli.run_app()`. Requires a running LiveKit server and valid environment variables.

### Run with LiveKit CLI options
```bash
python agent.py dev          # Development mode
python agent.py start        # Production mode
python agent.py connect      # Connect to specific room
```

### No test suite, linter, or CI/CD is configured.

## Required Environment Variables (.env)

```
OPENAI_API_KEY=...           # Required - OpenAI API access
LIVEKIT_URL=...              # Required - LiveKit server URL
LIVEKIT_API_KEY=...          # Required - LiveKit API key
LIVEKIT_API_SECRET=...       # Required - LiveKit API secret
INGEST_API_KEY=...           # Required - Webhook authentication key
PINECONE_API_KEY=...         # Required - Pinecone vector DB for treatment search
LLM_MODEL=gpt-4o-mini       # Optional - default: gpt-4o-mini
OPENROUTER_API_KEY=...       # Optional - for email summary generation via OpenRouter
PINECONE_REGION=us-east-1   # Optional - Pinecone region
INDEX_NAME=test              # Optional - Pinecone index name
DIMENSION=3072               # Optional - embedding dimension
EMBEDDING_MODEL=text-embedding-3-large  # Optional - OpenAI embedding model
DEBUG=false                  # Optional - verbose logging
```

## Architecture

### Framework & SDK Version
- **LiveKit Agents SDK** `1.2.14` — uses the **older** `agents.cli.run_app()` + `WorkerOptions(entrypoint_fnc=...)` pattern (not the newer `@server.rtc_session()` decorator from v1.3+)
- **Voice model**: OpenAI Realtime API (`gpt-realtime-mini-2025-10-06`) via `livekit-plugins-openai`
- All agents use `openai.realtime.RealtimeModel` — this is a speech-to-speech model, not a standard chat LLM

### Entry Point: `agent.py`
- Creates `AgentSession[UserData]`, starts `ConversationAgent` as initial agent
- Initializes **BitHuman avatar** (`lena.imx` model in project root, "essence" mode) via `bithuman.AvatarSession`
- Registers shutdown callback: saves local history + sends async webhook
- Safety net: extracts email from transcript via regex on disconnect (in case agent hadn't stored it yet)
- Hooks `user_input_transcribed` event for real-time translation

### 2-Agent Architecture

The system uses **2 agents** with a single handoff point:

```
ConversationAgent (greeting, consultation, lead qualification, contact collection)
  → CompletionAgent (email sending, summary, restart)
```

#### `ConversationAgent` (`agents/main_agent.py`)
The main brain. Extends `Agent` directly. Handles the full conversation lifecycle through 5 natural phases:

1. **Round 1 — Greeting**: Warm welcome, ask about treatment needs
2. **Round 2-3 — Consult + Soft Lead**: Answer questions + naturally try to get name/contact at end of response
3. **Ongoing — Build Lead**: Continue consulting, weave in contact collection, offer expert connection when ready
4. **After contact info — Consent**: Ask explicit GDPR consent to be contacted
5. **Wrap-up**: Confirm everything, hand off to CompletionAgent

**11 function tools:**

| Tool | Purpose |
|------|---------|
| `search_treatments(query, category, mentioned_treatments[])` | Semantic search via Pinecone RAG, send to frontend via `"products"` topic |
| `show_featured_products()` | Show curated product showcase from local data (once only, round 2) |
| `assess_lead_interest(score, level, reasoning)` | LLM stores its own lead assessment (0-10 score) — replaces keyword matching |
| `offer_expert_connection()` | Send Yes/No buttons via `"trigger"` topic |
| `handle_expert_response(accepted)` | Record customer's Yes/No response |
| `save_contact_info(name?, email?, phone?, preferred_contact?)` | Incremental contact collection — all params optional |
| `show_consent_buttons()` | Send GDPR consent Yes/No buttons via `"trigger"` topic |
| `record_consent(consent)` | GDPR consent to be contacted |
| `schedule_appointment(date, time)` | Save preferred appointment |
| `save_conversation_summary(summary)` | Agent-written conversation brief |
| `complete_contact_collection()` | Validate min info (name + email/phone + consent, + phone if "call me"), handoff → CompletionAgent |

#### `CompletionAgent` (`agents/email_agents.py`)
Transactional agent. Extends `BaseAgent`. Handles post-conversation tasks.

**3 function tools:**

| Tool | Purpose |
|------|---------|
| `send_appointment_emails(confirm)` | Send customer confirmation + lead notification to company |
| `send_summary_email(email?)` | Send conversation summary email |
| `start_new_conversation()` | Save history, send webhook, reset, restart |

#### `BaseAgent` (`agents/base.py`)
Shared foundation for sub-agents. Provides:
- `safe_generate_reply()` — retry wrapper for LLM calls (3x with backoff)
- `create_realtime_model()` — retry wrapper for model init (3x)
- Language injection — wraps prompts with language prefix/suffix
- `transcription_node()` — streams agent responses to frontend via `"message"` topic
- Data listener for language changes (`"language"` topic) and button responses (`"trigger"` topic) from frontend
- **Button-as-input (all buttons)**: ALL button clicks on the `"trigger"` topic are injected as user input via `session.generate_reply(user_input=value)`. "New conversation" buttons are matched against `_NEW_CONV_KEYS` (all 10 languages) and inject a restart phrase; all other buttons inject the button value directly. `ConversationAgent` has its own trigger handler for the same purpose.
- `save_conversation_summary()` function tool

### Session State: `core/session_state.py`
`UserData` dataclass — shared across agents via `AgentSession[UserData].userdata`:

```python
# Contact
name, email, phone, preferred_contact

# Appointment
schedule_date, schedule_time

# Lead (LLM-driven)
lead_score (0-10), lead_level (HOT/WARM/COOL/MILD), lead_reasoning

# Search
search_count, last_search_results

# Flow
expert_offered, expert_accepted, consent_given, consent_buttons_shown, featured_shown

# Conversation
conversation_summary, _history_saved
```

### Lead Scoring
Lead scoring is **LLM-driven** — the realtime model itself rates customer interest via `assess_lead_interest()` function tool. No hardcoded keyword lists. The LLM provides a 0-10 score, level, and reasoning based on the full conversation context. This works across all 10 languages without maintaining separate keyword lists.

### Configuration Layer: `config/`
All behavior is configuration-driven. Key files:
- `company.py` — **central company identity**: name, contact, address, social, mission (edit this to deploy for a new company)
- `agents.py` — agent name ("Lena"), role, personality, rules
- `settings.py` — LLM model, temperature, SMTP, webhook settings, CDN, debug flags
- `search.py` — Pinecone RAG search settings: hybrid alpha weighting, Flask port, search top-k, conversation limits
- `language.py` — `LanguageManager` singleton, 10 languages (en, de, tr, es, fr, it, pt, nl, pl, ar), runtime switching via LiveKit data channel, **default: German (de)**. Provides `get_language_prefix()`, `get_language_instruction()`, and `lang_hint()` for 3-layer language enforcement
- `products.py` — product domain, expertise areas, typo corrections
- `services.py` — expert title, service options, reachability labels
- `messages/` — all user-facing strings, organized by feature (agent, email, qualification, search, ui)
- `translations.py` — translation catalog for multi-language support

### Prompt Engineering: `prompt/`
All prompts are written in **English** — even when the agent responds in another language. Language directives (prefix/suffix) tell the LLM what language to speak in. This prevents language mixing.
- `static_main_agent.py` — `CONVERSATION_AGENT_PROMPT` (English, 5-phase flow, lead assessment guidelines, 10 tool specs) + `CONVERSATION_AGENT_GREETING`
- `static_workflow.py` — `BaseAgentPrompt` (English, shared foundation) + `COMPLETION_AGENT_PROMPT` (English)

### Data & Utilities: `utils/`
- `search_pipeline.py` — **Pinecone hybrid search** (`ProductSearchPipeline`). Connects to Pinecone vector DB, generates dense embeddings via OpenAI (`text-embedding-3-large`) + sparse embeddings via TF-IDF (`tfidf_vectorizer.joblib`), runs hybrid search with configurable alpha weighting (0.91 dense / 0.09 sparse). Key method: `pipeline.run(query, top_k=5)` → returns list of metadata dicts from Pinecone. Flask HTTP server (`/search`, `/health`) is available only when run as standalone (`python utils/search_pipeline.py`) — NOT loaded when imported by the agent
- `data_loader.py` — loads product data from **local files** (singleton `DataLoader`). Used for static prompt context (general info, FAQ). Local data files remain as reference but search is handled by Pinecone
- `webhook.py` — **async webhook** (`httpx.AsyncClient`) sends session data to `https://ayand-log.vercel.app/api/webhooks/ingest`. 3 retries, 5s timeout. Uses `COMPANY["name"]` from `config/company.py`
- `history.py` — saves conversations to `.txt` files in `history/` directory. `normalize_messages()` converts ChatMessage objects to `{role, message}` dicts
- `helpers.py` — email validation (`is_valid_email_syntax`) and time-based greeting (`get_greeting`)
- `smtp.py` — sends emails via Gmail SMTP (customer confirmation, lead notification, summary)

### Search Architecture: Pinecone RAG
Treatment search uses **Pinecone vector database** with hybrid (dense + sparse) search:
1. `ConversationAgent` initializes `ProductSearchPipeline` in `__init__()`
2. `search_treatments` tool calls `pipeline.run(query, top_k=5)` via `asyncio.to_thread()` (blocking call wrapped for async)
3. Pinecone returns metadata dicts with treatment info (`name`, `Introduction`, `Features`, `Benefits to Clients`, `url`, `image_link`)
4. Results are formatted for both LLM context and frontend display
5. Frontend receives product cards via `"products"` topic with `image_link` from Pinecone metadata

### Webhook & Conversation Persistence
On session end (user disconnect or normal completion):
1. **Safety net**: regex extracts email from transcript if not yet stored in UserData
2. **Local save**: `save_conversation_to_file()` writes `.txt` transcript to `history/`
3. **Async webhook**: `send_session_webhook()` POSTs transcript, contact info, and agent-written summary to ingest endpoint

The conversation summary is generated by the **realtime model itself** via `save_conversation_summary()` function tool during the conversation — no separate LLM API call. This keeps shutdown fast (~5s total, well within LiveKit's 10s shutdown timeout).

Webhook payload structure:
```json
{
  "apiKey": "INGEST_API_KEY",
  "companyName": "Beauty Lounge Warendorf",
  "sessions": [{
    "sessionId": "...",
    "date": "ISO timestamp",
    "durationSeconds": 123,
    "transcript": [{"role": "user|assistant", "content": "..."}],
    "contactInfo": {
      "name", "email", "phone", "schedule",
      "potentialScore" (0-100), "status" (hot_lead/warm_lead/cool_lead/mild_lead),
      "reachability", "conversationBrief"
    }
  }]
}
```

### Frontend Communication
Agent communicates with the web frontend via **LiveKit Room Topics** (JSON payloads):

| Topic | Direction | Content |
|-------|-----------|---------|
| `"message"` | Agent → Frontend | `{"agent_response": "text"}` |
| `"products"` | Agent → Frontend | `[{product details}]` |
| `"trigger"` | Agent → Frontend | `{"Ja": "Ja", "Nein": "Nein"}` (buttons) |
| `"trigger"` | Frontend → Agent | Button click response (key from button payload) |
| `"language"` | Frontend → Agent | `{"language": "de"}` |
| `"clean"` | Agent → Frontend | `{"clean": true}` (reset UI) |

Buttons are shown for:
- **Expert offer** (Yes/No) — when offering to connect with Patrizia. Guarded: only sent once (`expert_offered` flag)
- **GDPR consent** (Yes/No) — when asking permission to use contact info. Guarded: only sent once (`consent_buttons_shown` flag)
- **Appointment confirmation** (Yes/No) — only shown if `schedule_date` or `schedule_time` exist in UserData. Skipped entirely if no appointment was scheduled.
- **Summary offer** (Yes/No) — when offering to email conversation summary. Shown by `send_appointment_emails` tool return or directly by `on_enter()` when no appointment.
- **New conversation** — restart button after conversation ends

All button clicks are injected as user text input via `session.generate_reply(user_input=value)` — users can click buttons OR speak, both work.

### Key Patterns
- **Tool return values**: **ALL** function tools (including CompletionAgent) return **English** instruction strings with `lang_hint()` appended (e.g. `f"Saved. Continue naturally. {lang_hint()}"`). This is critical — the OpenAI Realtime API does not reliably generate follow-up speech when a tool returns `None` (per LiveKit docs: "Return None to complete the tool silently without requiring a reply from the LLM"). CompletionAgent tools return descriptive strings that tell the LLM what to do next (e.g. "Appointment confirmed and emails sent. Now offer summary..."). No tools use `_safe_reply()` — all rely on return strings for LLM continuity.
- **Featured product showcase**: On round 2, agent calls `show_featured_products()` once to display a curated mix of treatments from local data files (3 treatments + 2 PMU + 2 wellness). Frontend auto-replaces these when `search_treatments` sends RAG results later. Guarded by `featured_shown` flag to prevent repeats.
- **Proactive product display**: The prompt instructs the agent to call `search_treatments` for ANY treatment-related mention — including vague/general questions like "Was bieten Sie an?". Products should be shown as often as possible. The only exceptions are pure greetings without treatment interest, thanks/goodbye, and completely unrelated topics.
- **Retry with backoff**: `safe_generate_reply()` retries LLM calls 3x; `create_realtime_model()` retries model init 3x
- **Language injection (3-layer enforcement)**: (1) `get_language_prefix()` — "LANGUAGE LOCK" tag prepended to every prompt, (2) `get_language_instruction()` — detailed directive with "ABSOLUTE LANGUAGE LOCK" and "PERMANENT" rule appended after every prompt, (3) `lang_hint()` — short `[LANGUAGE: X]` reminder on every tool return. All directives include "IGNORE the language of ALL previous messages" and "NEVER switch to another language" in the target language. Language switch uses `_lang_listener_active` guard to prevent stale listeners after agent handoff
- **Transcription streaming**: `BaseAgent.transcription_node()` streams agent responses to frontend in real-time via room topic
- **LLM-driven lead scoring**: The realtime model judges customer interest via function tool — no hardcoded keyword lists
- **Contact collection rules**: Name + (email OR phone) + consent required for handoff. If user says "call me" → `preferred_contact="phone"` is set and phone becomes mandatory. Prompt-driven detection via `save_contact_info(preferred_contact="phone")`.
- **Proactive lead capture**: From round 2-3, agent answers the question AND naturally asks for name/contact at the end
- **GDPR consent**: Agent calls `show_consent_buttons()` to display Yes/No buttons (guarded by `consent_buttons_shown` flag — only once), then asks verbally. Both button click and voice response are accepted. Consent must be recorded via `record_consent()` before handoff
- **Agent-written summary**: `save_conversation_summary()` function tool lets the realtime model write conversation briefs during the conversation (no separate LLM call needed)
- **Button-as-input (all buttons)**: Both `BaseAgent._handle_data_received()` and `ConversationAgent._handle_data_received()` listen for `"trigger"` topic responses. "New conversation" keys (matched against `_NEW_CONV_KEYS` from all 10 languages) inject a restart phrase. All other button clicks inject the button VALUE as user input via `generate_reply(user_input=value)`. This means clicking a button works identically to speaking the answer.
- **Listener deactivation on handoff**: Both `complete_contact_collection()` (ConversationAgent → CompletionAgent) and `start_new_conversation()` (CompletionAgent → fresh ConversationAgent) set `_lang_listener_active = False` before returning the new agent, preventing stale listeners from processing events meant for the new agent
- **Conditional CompletionAgent flow**: `CompletionAgent.on_enter()` checks `schedule_date`/`schedule_time`. If appointment exists → shows appointment confirmation buttons. If no appointment → skips directly to summary offer buttons. The prompt mirrors this logic.
- **Safety net on disconnect**: Regex extracts email from transcript if user disconnects before agent stores it

## Logging
- Log files: `docs/app_YYYYMMDD_HHMMSS.log`
- Conversation history: `history/` directory (`.txt` transcripts)
- Noisy loggers (httpx, openai, livekit) suppressed to WARNING level
