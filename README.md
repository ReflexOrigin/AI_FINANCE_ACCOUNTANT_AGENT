# AI_FINANCE_ACCOUNTANT_AGENT

**AI_FINANCE_ACCOUNTANT_AGENT** is an open-source, modular, and extensible voice‑activated finance accountant agent built with FastAPI, open-source LLMs, Whisper STT, FAISS‑powered RAG, and more. It enables dynamic financial operations via voice commands, with a plugin‑style architecture for easy addition of new features.

## Features

- **Voice Commands:** Speech‑to-text via Whisper; text‑to-speech via Mozilla or pyttsx3.
- **Intent Recognition:** Finance‑specific intent parsing using an open‑source LLM.
- **Dynamic Operations:** Modular handlers for investor relations, cash management, accounting, tax reporting, and more.
- **Retrieval‑Augmented Generation:** FAISS + sentence‑transformers to query and augment LLM responses with company documents.
- **Banking Adapters:** Dummy or real banking API layer for balances, transactions, transfers, and portfolios.
- **Security:** JWT authentication, input sanitization, rate limiting, and audit logs.
- **Performance:** Quantized LLM inference (4‑bit/8‑bit), async I/O, and configurable timeouts.

## Prerequisites

- Python 3.10+
- Git
- FFmpeg (for audio processing)
- Environment capable of running quantized LLMs (GPU recommended for larger models)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ReflexOrigin/AI_FINANCE_ACCOUNTANT_AGENT.git
   cd AI_FINANCE_ACCOUNTANT_AGENT
   ```
2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Windows
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Agent

Start the FastAPI server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Explore the interactive API docs at `http://localhost:8000/docs`.

## Adding New Operations

1. Create `modules/operations/<your_domain>.py`.
2. Define `async def handle_<subintent>(entities: Dict) -> Dict` functions.
3. Restart the server; `OperationManager` auto‑discovers your handlers.


## License

This project is licensed under the MIT License.

## Project Structure

```
AI_FINANCE_ACCOUNTANT_AGENT/
├── config/
│   └── settings.py
├── modules/
│   ├── bank_adapters.py
│   ├── file_manager.py
│   ├── intent_recognition.py
│   ├── llm_module.py
│   ├── operation_manager.py
│   ├── rag_module.py
│   ├── response_generation.py
│   ├── security.py
│   ├── voice_input.py
│   └── operations/
│       ├── investor_relations.py
│       ├── cash_management.py
│       ├── risk_management.py
│       ├── investment_management.py
│       ├── fin_inst_relations.py
│       ├── external_financing.py
│       ├── accounting.py
│       ├── mis.py
│       ├── ar_aging.py
│       ├── ap_aging.py
│       ├── tax_reporting.py
│       └── financial_planning.py
└── main.py
```

