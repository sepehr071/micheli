# Migration Guide: Hanshow → Beauty Lounge Warendorf

This document describes every file and change needed to adapt the current Hanshow Technology voice AI agent for **Beauty Lounge Warendorf** — a cosmetics studio in Warendorf, Germany.

## New Company Profile

| Field | Value |
|-------|-------|
| **Name** | Beauty Lounge Warendorf |
| **Owner** | Patrizia Miceli |
| **Address** | Mühlenstraße 1, 48231 Warendorf, Germany |
| **Website** | https://beauty-lounge-warendorf.de |
| **Type** | Cosmetics studio (Kosmetikstudio) — B2C |
| **Services** | Facial treatments, body treatments, permanent makeup, foot care (Fußpflege), manicures, massages, body peeling, Forma radio frequency, Brigitte Kettner natural cosmetics |
| **Philosophy** | Holistic beauty, natural cosmetics, sustainability, individualized treatments |
| **Booking** | Via Planity |
| **Primary language** | German |

## Decisions

- **Agent name**: Keep "Lena"
- **Languages**: Keep all 10
- **Lead qualification flow**: Keep full flow (qualification → contact → email)
- **Service data**: Will be provided separately by owner — use placeholders until then

---

## TIER 1 — Company & Product Identity (full rewrite)

### `config/company.py`
**Change ~90% of file (~70 lines)**

| Current value | New value |
|---------------|-----------|
| `name`: "Hanshow" | "Beauty Lounge Warendorf" |
| `full_name`: "Hanshow Technology" | "Beauty Lounge Warendorf" |
| `description`: "Digital Retail Solutions" | "Kosmetikstudio & Beauty" |
| `website`: "hanshow.com" | "beauty-lounge-warendorf.de" |
| `language`: "English" | "German" |
| `timezone`: "Europe/Berlin" | "Europe/Berlin" (keep) |
| All office locations (7 countries) | Single location: Mühlenstraße 1, 48231 Warendorf |
| Social media URLs | Beauty Lounge Instagram/Facebook |
| Lead notification emails | Patrizia's email |
| Email closing signature | "Ihr Beauty Lounge Team" |
| Company mission | Patrizia's philosophy: holistic beauty, natural cosmetics, sustainability |
| Founded year, HQ info | Founded 2005, Warendorf |

### `config/products.py`
**Full rewrite — 100% of file (~103 lines)**

| Current | New |
|---------|-----|
| `domain`: "Digital Retail Solutions" | "Kosmetik & Beauty-Behandlungen" |
| `specialties`: ESL, Digital Signage, Smart Retail, AI-powered, IoT | Gesichtsbehandlungen, Körperbehandlungen, Permanent Make-Up, Fußpflege, Massagen, Apparative Kosmetik |
| `categories`: 11 Hanshow product categories | Treatment categories: Gesicht, Körper, Hände & Füße, Permanent Make-Up, Wellness/Massage |
| `product_lines`: Nebular, Nebular Pro, Polaris, etc. | Treatment lines: Klassische Kosmetik, Apparative Kosmetik (Forma), Brigitte Kettner Methode, Permanent Make-Up |
| `domain_keywords`: ESL/retail terms (17 items) | Beauty terms: kosmetik, behandlung, gesicht, haut, pflege, peeling, massage, permanent, makeup, maniküre, pediküre, fußpflege, lifting, anti-aging, kollagen, etc. |
| `product_keywords`: nebular, polaris, lumina, etc. | Treatment keywords: forma, brigitte kettner, microneedling, radiofrequenz, etc. |
| `typo_corrections`: 18 Hanshow product misspellings | Common beauty misspellings: "permanet" → "permanent", "manikure" → "maniküre", "pedikure" → "pediküre", "masage" → "massage", etc. |

### `config/agents.py`
**Change ~30% of file (~47 lines)**

| Current | New |
|---------|-----|
| `name`: "Lena" | "Lena" (keep) |
| `role`: "Product Consultant" | "Beauty-Beraterin" |
| Golden rules: "Be knowledgeable about ESL, digital retail, and IoT technology" | "Be knowledgeable about cosmetic treatments, skincare, and beauty services" |
| Expertise references `PRODUCTS["specialties"]` | Auto-updates (no manual change needed) |

### `config/metadata.py`
**Full rewrite — 100% of product-specific sections (~229 lines)**

| Current fields | New fields |
|----------------|-----------|
| `display_size_inch` (numeric) | `duration_minutes` (numeric: 30, 60, 90, 120) |
| `product_line` (categorical: Nebular, Polaris, etc.) | `treatment_category` (categorical: Gesicht, Körper, Hände & Füße, Permanent Make-Up, Wellness) |
| `display_color` (BW, BWR, BWRY, LCD) | `skin_type` (Normal, Trocken, Fettig, Mischhaut, Empfindlich) |
| `nfc_support` (Yes/No) | `first_time_suitable` (Yes/No) |
| `category` (nebular, other, use_cases) | `method` (Klassisch, Apparativ, Brigitte Kettner, Permanent) |
| Aliases: 37 product name variations | Aliases: treatment name variations in German |
| Implicit mappings: small→size, large→size, color, nfc | Implicit mappings: kurz→30min, lang→90min+, gesicht→Gesicht category, etc. |

---

## TIER 2 — Buying Signals & Classification (domain keywords)

### `config/signals.py`
**Full rewrite — 100% of keyword content (~65 lines)**

| Current HOT signals | New HOT signals |
|--------------------|--------------------|
| "price", "quote", "demo", "order", "purchase", "deploy", "budget", "contract" | "termin", "buchen", "preis", "kosten", "sofort", "nächste woche", "gutschein", "permanent makeup termin" |

| Current WARM signals | New WARM signals |
|---------------------|---------------------|
| "nebular", "polaris", "lumina", "smartcart", "esl", "electronic shelf", "nfc", "battery", "retail", "store" | Treatment names (gesichtsbehandlung, peeling, massage, fußpflege, forma, anti-aging), skin concerns (falten, unreinheiten, trockene haut, augenringe), specific asks (empfehlung, beratung, hauttyp) |

| Current COOL signals | New COOL signals |
|---------------------|---------------------|
| Generic browsing terms | "mal schauen", "informieren", "was bietet ihr an", "welche behandlungen" |

### `config/classification.py`
**Rewrite ~70% of file (~160 lines)**

All regex patterns referencing product names must change:

| Current patterns | New patterns |
|-----------------|-------------|
| `nebular\|polaris\|lumina\|smartcart\|spatrol` | `gesichtsbehandlung\|fußpflege\|massage\|peeling\|permanent.?make.?up\|maniküre\|forma` |
| `esl\|electronic shelf label\|digital price tag` | `kosmetik\|behandlung\|hautpflege\|beauty` |
| `supermarket\|retail\|store\|shop` | `studio\|salon\|termin\|sitzung` |
| Technical words: esl, lcd, nfc, rfid, ip68, ip65 | Beauty-specific technical words: radiofrequenz, kollagen, hyaluron, microneedling, dermapen |
| Single-attribute words: 11 product names | Single-attribute words: treatment type names |

### `config/prompt_settings.py`
**Rewrite ~60% of file (~113 lines)**

| Section | Change |
|---------|--------|
| Template word limits | Keep as-is (generic) |
| Expert phrases (German) | Rewrite all 6 categories. Example: "Unser Verkaufsexperte kann die Verfügbarkeit sofort prüfen" → "Unsere Kosmetikerin Patrizia kann Sie persönlich beraten und den perfekten Behandlungsplan erstellen" |
| Signal triggers | Replace: "preis", "kosten", "finanzierung", "leasing" → "preis", "kosten", "gutschein", "angebot". Replace "probefahrt", "anschauen" → "probetermin", "ausprobieren", "testen" |

---

## TIER 3 — Prompts (the core personality)

### `prompt/static_main_agent.py`
**Full rewrite — 100% of file (~279 lines). This is the most critical file.**

What to remove:
- `_NEBULAR_OVERVIEW` (15-year battery, IP68, unibody design, display sizes)
- `_NEBULAR_PRO_OVERVIEW` (multicolor, BWRY, geolocation, OTA firmware)
- `_OTHER_PRODUCTS_OVERVIEW` (AI Plus, All-Star Cloud, Digital Energy, SmartCart, SPatrol — 9 products)
- `_USE_CASES_OVERVIEW` (Leroy Merlin, Spar case studies)
- All "DEFAULT INDUSTRY FOCUS - BEAUTY/COSMETICS RETAIL" sections (appears 8 times — these are about ESL products *for* beauty retail, NOT about beauty services)

What to write:
- `_TREATMENTS_OVERVIEW` — facial treatments, body treatments, hand/foot care
- `_PERMANENT_MAKEUP_OVERVIEW` — eyebrows, lips, eyeliner procedures
- `_APPARATIVE_OVERVIEW` — Forma radio frequency, Brigitte Kettner method
- `_WELLNESS_OVERVIEW` — massages, body peeling, relaxation treatments
- `BEAUTY_LOUNGE_PROMPT` — Lena as Beauty-Beraterin for Beauty Lounge Warendorf, Patrizia's philosophy (holistic beauty, natural cosmetics, sustainability), treatment knowledge, warm/welcoming tone for B2C clients
- `BEAUTY_LOUNGE_GREETING` — Welcome message mentioning Beauty Lounge, Warendorf, available treatments
- Tool calling instructions referencing new treatment categories instead of "nebular"/"other"/"use_cases"

### `prompt/static_extraction.py`
**Rewrite ~60% of file (~185 lines)**

| Current | New |
|---------|-----|
| "filter extractor for a {LANGUAGE} {PRODUCT_DOMAIN} dealership" | "filter extractor for a {LANGUAGE} beauty and cosmetics studio" |
| Categorical specs from metadata.py | Auto-updates when metadata.py changes |
| 7 examples about cars: "red SUV under 30.000", "Family car with 7 seats" | Beauty examples: "Gesichtsbehandlung für trockene Haut", "Kurze Massage unter einer Stunde", "Permanent Make-Up für Augenbrauen" |

### `prompt/dynamic_prompts.py`
**Rewrite ~70% of file (~324 lines)**

| Current | New |
|---------|-----|
| `_singular` → "Fahrzeug"/"Produkt" | "Behandlung" |
| `_domain` → "Gebrauchtwagen"/"Digital Retail Solutions" | "Kosmetik & Beauty" |
| Examples: "SUV, Kombi oder Limousine?" | "Gesichtsbehandlung, Massage oder Fußpflege?" |
| All PROMPT_TEMPLATES (8 templates) | Rewrite with beauty terminology and examples |

### `prompt/static_workflow.py`
**Minimal changes (~15% of ~206 lines)**

- BaseAgentPrompt references `MAIN_AGENT['name']`, `COMPANY['full_name']`, `PRODUCTS['domain']` — these auto-update via config
- Check for any remaining hardcoded ESL/Hanshow text and replace
- Sub-agent prompts (GetUserName, Email, Qualification) are generic — no changes needed

---

## TIER 4 — Messages & Translations

### `config/messages/search.py`
**Full rewrite ~90% of file (~159 lines)**

| Section | Change |
|---------|--------|
| SIGNAL_INSTRUCTIONS (8 German blocks) | Replace "Fahrzeuge" (vehicles) with "Behandlungen". Replace ESL/product references with beauty treatment context. Keep structure but rewrite all German content |
| EXPERT_QUESTION_INSTRUCTION | Update for beauty context: "Möchten Sie einen persönlichen Beratungstermin?" |
| CONVERSATION_RULES | Keep structure, update product references |
| BUDGET_INJECTIONS (5 German prompts) | Adapt for beauty pricing context or remove if not applicable |
| RELAXATION_MESSAGES (8 German messages) | Replace product color/feature references with treatment availability messages: "Diese Behandlung ist aktuell nicht verfügbar, aber wir haben ähnliche Alternativen..." |

### `config/messages/email.py`
**Update ~40% of file (~382 lines)**

| Section | Change |
|---------|--------|
| Email subjects (4 languages) | Update: "Hanshow" → "Beauty Lounge Warendorf" |
| Email bodies (4 languages) | Update company branding, closing signature |
| Lead notification format | Update field labels if needed (remove product-specific fields like "Lead Degree" if not relevant) |
| `{COMPANY['email_closing']}` | Auto-updates from company.py |

### `config/translations.py`
**Update ~30% of file (~516 lines)**

| Section | Change |
|---------|--------|
| `expert_title` (10 languages) | "Product Consultant" → "Kosmetikerin" (de), "Beauty Consultant" (en), etc. |
| `expert_title_alt` (10 languages) | "Solutions Specialist" → "Beauty-Beraterin" (de), "Beauty Advisor" (en), etc. |
| `primary_service` (10 languages) | "Demo"/"Probefahrt" → "Beratungstermin"/"Consultation" |
| `service_options` (10 languages) | Replace "demo, pricing, browsing" → "Beratung, Terminbuchung, Behandlungsinfo" |
| `off_topic_redirect` | Update `{domain}` reference (auto-updates) |

### `config/messages/history.py`
**Minimal — change agent name**

| Current | New |
|---------|-----|
| `[BERTA]:` | `[LENA]:` |

### `config/services.py`
**Update ~40% of file (~155 lines)**

| Section | Change |
|---------|--------|
| Expert titles (10 languages) | Same as translations.py updates above |
| Primary service | "Demo"/"Probefahrt" → "Beratungstermin" |
| Service options | Replace B2B options (demo, pricing quote, browsing) → B2C options (Beratung, Terminbuchung, Behandlungsinfo) |
| Reachability options | Keep Phone, WhatsApp, Email — these work for beauty studio too |

---

## TIER 5 — Data & Infrastructure

### `config/settings.py`
**Minimal — ~5% (~54 lines)**

| Current | New |
|---------|-----|
| `IMAGE_CDN_BASE_URL`: "https://image.ayand.cloud/Images/" | New CDN URL or remove if no product images needed |
| `RT_MODEL`: "gpt-realtime-mini-2025-10-06" | Keep (same voice model) |
| SMTP config | Keep or update with Beauty Lounge email credentials |

### `config/search.py`
**Update file paths (~15% of ~40 lines)**

| Current paths | New paths |
|--------------|-----------|
| `data/hanshow-products/nebular/nebular.txt` | `data/beauty-services/treatments/treatments.txt` |
| `data/hanshow-products/other/other.txt` | `data/beauty-services/permanent-makeup/permanent-makeup.txt` |
| `data/hanshow-products/use_cases/use_cases.txt` | `data/beauty-services/wellness/wellness.txt` |
| `data/general_info/general_info.txt` | `data/general_info/general_info.txt` (update content) |
| `data/FAQ/FAQ.txt` | `data/FAQ/FAQ.txt` (update content) |

### `utils/data_loader.py`
**Update ~20% of file (~596 lines)**

| Current | New |
|---------|-----|
| `IMAGE_BASE_URL`: "https://image.ayand.cloud/hanshow-images/" | New URL or remove |
| Data categories: `NEBULAR`, `OTHER`, `USE_CASES` | `TREATMENTS`, `PERMANENT_MAKEUP`, `WELLNESS` (or similar) |
| File paths: "hanshow-products/..." | "beauty-services/..." |
| `DataClassifier` categories | Update for beauty treatment classification |

### `utils/filter_extraction.py`
**Update filter logic for beauty domain**

Replace ESL product attribute extraction (display size, NFC, color) with beauty service attributes (treatment type, duration, skin type, body area).

### `utils/filter_state.py`
**Update UserPreferences fields**

| Current fields | New fields |
|----------------|-----------|
| `price_range` | `price_range` (keep) |
| `categories` (nebular/other) | `categories` (gesicht/körper/hände/permanent/wellness) |
| `features` (NFC, IP68, battery) | `preferences` (naturkosmetik, apparativ, entspannung) |
| Display-specific fields | `duration_preference`, `skin_type`, `treatment_area` |

### `data/` directory
**Create new data files** (content to be provided by owner)

```
data/
├── beauty-services/
│   ├── treatments/treatments.txt        # Facial & body treatment descriptions
│   ├── permanent-makeup/permanent-makeup.txt  # PMU service descriptions
│   └── wellness/wellness.txt            # Massage, peeling, relaxation
├── general_info/general_info.txt        # About Beauty Lounge, Patrizia, philosophy
└── FAQ/FAQ.txt                          # Common questions about beauty services
```

---

## NO CHANGES NEEDED

These files are domain-agnostic and work as-is:

| File | Why no changes |
|------|---------------|
| `config/language.py` | Language infrastructure is generic — manages 10 languages without domain content |
| `core/lead_scoring.py` | Pure scoring math — reads keywords from `config/signals.py` |
| `core/response_builder.py` | Template assembly — reads from `config/messages/` |
| `core/session_state.py` | `UserData` dataclass — field names are generic (email, phone, name, ret_car, signal_level) |
| `agents/base.py` | Framework code — retry logic, language injection, transcription streaming |
| `agents/main_agent.py` | Imports from config — only change if class is renamed |
| `agents/qualification_agents.py` | Generic qualification flow — asks timing, next step, reachability |
| `agents/contact_agents.py` | Generic contact collection — name, email, phone, schedule |
| `agents/email_agents.py` | Generic email dispatch and summary |
| `agent.py` | Entrypoint — only update import if `HanshowAssistant` is renamed |
| `utils/smtp.py` | Generic SMTP sender |
| `utils/history.py` | Generic conversation save logic |
| `utils/message_classifier.py` | Reads patterns from `config/classification.py` — no direct changes |

---

## Summary

| Priority | Files | Effort |
|----------|-------|--------|
| **TIER 1** — Identity | `company.py`, `products.py`, `agents.py`, `metadata.py` | 4 files, ~450 lines |
| **TIER 2** — Keywords | `signals.py`, `classification.py`, `prompt_settings.py` | 3 files, ~340 lines |
| **TIER 3** — Prompts | `static_main_agent.py`, `static_extraction.py`, `dynamic_prompts.py`, `static_workflow.py` | 4 files, ~790 lines |
| **TIER 4** — Messages | `search.py`, `email.py`, `translations.py`, `history.py`, `services.py` | 5 files, ~1,210 lines |
| **TIER 5** — Data/Infra | `settings.py`, `search.py`, `data_loader.py`, `filter_extraction.py`, `filter_state.py`, `data/` | 6 files + new data |
| **No change** | 13 files | 0 lines |

**Total**: ~22 files to modify, ~2,800 lines affected out of ~7,500 total.
**Recommended order**: Tier 1 → Tier 2 → Tier 3 → Tier 5 → Tier 4 (messages last since they reference config values).
