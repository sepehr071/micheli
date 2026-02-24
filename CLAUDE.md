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
LLM_MODEL=gpt-4o-mini       # Optional - default: gpt-4o-mini
OPENROUTER_API_KEY=...       # Optional - for email summary generation via OpenRouter
DEBUG=false                  # Optional - verbose logging
```

## Architecture

### Framework & SDK Version
- **LiveKit Agents SDK** `1.2.14` — uses the **older** `agents.cli.run_app()` + `WorkerOptions(entrypoint_fnc=...)` pattern (not the newer `@server.rtc_session()` decorator from v1.3+)
- **Voice model**: OpenAI Realtime API (`gpt-realtime-mini-2025-10-06`) via `livekit-plugins-openai`
- All agents use `openai.realtime.RealtimeModel` — this is a speech-to-speech model, not a standard chat LLM

### Entry Point: `agent.py`
- Creates `AgentSession[UserData]`, starts `BeautyLoungeAssistant` as initial agent
- Registers shutdown callback: saves local history + sends async webhook
- Safety net: extracts email from transcript via regex on disconnect (in case agent hadn't stored it yet)
- Hooks `user_input_transcribed` event for real-time translation

### Agent Chain (Handoff Pattern)
Agents hand off control sequentially via `session.update_agent()`:

```
BeautyLoungeAssistant (main conversation + treatment search)
  → PurchaseTimingAgent (Q1: when buying?)
    → NextStepAgent (Q2: what next step?)
      → ReachabilityAgent (Q3: how to reach?)
        → GetUserNameAgent
          → GetUserEmailPhoneAgent
            → ScheduleCallAgent
              → SendEmailAgent
                → SummaryAgent
                  → LastAgent (restart or end)
```

- `BeautyLoungeAssistant` (`agents/main_agent.py`) — extends `Agent` directly, has `@function_tool` methods for product retrieval, conversation summary, and expert connection
- All sub-agents (`agents/qualification_agents.py`, `agents/contact_agents.py`, `agents/email_agents.py`) — extend `BaseAgent` (`agents/base.py`) which wraps `Agent` with retry logic, language injection, and frontend transcription streaming

### Session State: `core/session_state.py`
- `UserData` dataclass — shared across all agents via `AgentSession[UserData].userdata`
- Holds: contact info, search results, signal levels, qualification responses, conversation summary, flow control flags
- `conversation_summary` — written by the realtime model via `save_conversation_summary()` function tool (no separate LLM call)
- In-memory only; saved to file + webhook on shutdown

### Configuration Layer: `config/`
All behavior is configuration-driven. Key files:
- `company.py` — **central company identity**: name, contact, address, social, mission (edit this to deploy for a new company)
- `agents.py` — agent name ("Lena"), role, personality, rules
- `settings.py` — LLM model, temperature, SMTP, webhook settings, CDN, debug flags
- `language.py` — `LanguageManager` singleton, 10 languages (en, de, tr, es, fr, it, pt, nl, pl, ar), runtime switching via LiveKit data channel
- `signals.py` — buying signal keywords (HOT/WARM/COOL) and lead scoring weights
- `products.py` — product domain, expertise areas, typo corrections
- `messages/` — all user-facing strings, organized by feature (agent, email, qualification, search, ui)
- `translations.py` — translation catalog for multi-language support

### Prompt Engineering: `prompt/`
- `static_main_agent.py` — main agent system prompt and greeting
- `static_workflow.py` — sub-agent workflow prompts
- `static_extraction.py` — data extraction prompts (contact info, filters)
- `dynamic_prompts.py` — runtime prompt generation based on context and language

### Business Logic: `core/`
- `lead_scoring.py` — detects buying signals (HOT/WARM/COOL/MILD) from user messages, calculates lead degree score (0-10)
- `response_builder.py` — assembles signal-aware LLM instructions, tracks response budget

### Data & Utilities: `utils/`
- `data_loader.py` — loads product data from **local files** (singleton `DataLoader`), NOT from Pinecone/RAG despite README claims
- `webhook.py` — **async webhook** (`httpx.AsyncClient`) sends session data to `https://ayand-log.vercel.app/api/webhooks/ingest`. 3 retries, 5s timeout. Uses `COMPANY["name"]` from `config/company.py`
- `history.py` — saves conversations to `.txt` files in `history/` directory. `normalize_messages()` converts ChatMessage objects to `{role, message}` dicts (used by both history and webhook)
- `message_classifier.py` — classifies user intent into `MessageCategory` enum (search, greeting, buying_signal, off_topic, etc.)
- `filter_extraction.py` / `filter_state.py` — extracts and tracks user preference filters
- `smtp.py` — sends emails via Gmail SMTP (customer confirmation, lead notification, summary)

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
      "purchaseTiming", "potentialScore", "nextStep",
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
| `"trigger"` | Agent → Frontend | `{"Yes": "Yes", "No": "No"}` (buttons) |
| `"language"` | Frontend → Agent | `{"language": "de"}` |
| `"clean"` | Agent → Frontend | `{"clean": true}` (reset UI) |

### Key Patterns
- **Retry with backoff**: `safe_generate_reply()` retries LLM calls 3x; `create_realtime_model()` retries model init 3x
- **Language injection**: Every prompt is wrapped with language prefix + suffix to ensure LLM responds in correct language
- **Transcription streaming**: `BaseAgent.transcription_node()` streams agent responses to frontend in real-time via room topic
- **Signal-driven flow**: Buying signal level determines when to offer expert connection (requires 2+ searches + HOT/WARM signal)
- **Agent-written summary**: `save_conversation_summary()` function tool lets the realtime model write conversation briefs during the conversation (no separate LLM call needed)
- **Safety net on disconnect**: Regex extracts email from transcript if user disconnects before agent stores it

## Logging
- Log files: `docs/app_YYYYMMDD_HHMMSS.log`
- Conversation history: `history/` directory (`.txt` transcripts)
- Noisy loggers (httpx, openai, livekit) suppressed to WARNING level
