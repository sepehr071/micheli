# Herbrand Berta AI Assistant

Berta is a real-time voice AI assistant powered by LiveKit Agents for the Herbrand used car dealership website. She helps German-speaking customers find used cars (e.g., Mercedes V-Class vans, SUVs, electrics) via natural conversation. Uses hybrid RAG search over Pinecone vector DB with semantic filtering on metadata like price, mileage, features (e.g., Panoramadach, Allrad).

## Features
- **Real-time Voice Interaction**: GPT Realtime model (`gpt-realtime-mini-2025-10-06`) for low-latency German responses.
- **Semantic Car Search**: Query expansion, attribute extraction (LLM), hybrid dense/sparse (TF-IDF + OpenAI embeddings) Pinecone retrieval.
- **Advanced Filtering**: Supports 50+ metadata fields (price_eur, mileage_km, has_SeatHeating, usage_Family, etc.).
- **Frontend Integration**: Sends JSON payloads via LiveKit room topics (`products`, `message`) with product details, prices, and images (cover-first from `https://image.ayand.cloud`).
- **Empathetic Persona**: Friendly female assistant focused on family/safety/eco needs.

## Architecture
- **RAG Pipeline**: `ProductSearchPipeline` in `utils/pinecoin.py` (Pinecone index, TF-IDF sparse, OpenAI dense).
- **Prompts**: Centralized in `prompt/prompts.py` (BERTA_PROMPT, extraction).
- **Utils**: Query utils (`utils/utils.py`), image paths (`utils/image_utils.py`).
- **Config**: Env vars and metadata filters (`config/config.py`).

## Quick Start

### Prerequisites
- Python 3.10+
- LiveKit account/room setup (connect via `agents.cli.run_app`).
- Pinecone index (`test` or env `INDEX_NAME`) with vehicle vectors/metadata.
- `tfidf_vectorizer.joblib` (pre-trained, in repo).

### Installation
```bash
pip install -r req.txt
```

### Environment Variables (.env)
```
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_REGION=europe-west4  # optional
EMBEDDING_MODEL=text-embedding-3-large
INDEX_NAME=test
DIMENSION=3072
LLM_MODEL=gpt-4o-mini  # for utils
DEBUG=true  # optional
```
*(LlamaCloud vars optional/not used in core pipeline)*

### Run
```bash
python agent.py
```
- Starts LiveKit worker.
- Connect client to room; Berta greets and awaits queries.
- Test: "Ich suche einen Familien-SUV unter 30.000€ mit Navi."

## Project Structure
```
.
├── agent.py              # LiveKit Agent entrypoint & _retrieve_products tool
├── req.txt               # Dependencies
├── tfidf_vectorizer.joblib  # Pre-trained sparse vectorizer
├── config/
│   └── config.py         # Metadata filters, LlamaCloud (legacy)
├── prompt/
│   └── prompts.py        # LLM prompts (extraction, Berta instructions)
└── utils/
    ├── pinecoin.py       # ProductSearchPipeline (Pinecone RAG)
    ├── utils.py          # Query expansion, attribute extraction
    └── image_utils.py    # Image path fetching (cover first)
```

## Development
- **Logs**: Pipeline logs to `docs/pipeline.log`.
- **Tune Search**: Adjust `alpha=0.71` in `run()`, `top_k=5`.
- **Add Filters**: Extend `SUPPORTED_FILTERS` in `config.py`.
- **Frontend**: Listen to room topics `products` (array of {url, image[], product_name, price}) and `message` ({agent_response}).


