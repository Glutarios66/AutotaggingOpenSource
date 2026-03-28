# AutotaggingOpenSource

An open-source API for automatic accessibility enhancement of documents using Generative AI.

Upload a document via the API and receive an accessibility-enhanced, tagged version in return — including a WCAG score and detailed audit report.

---

## Prerequisites

Make sure the following is installed on your system:

- Python 3.11 or newer → https://www.python.org/downloads/
- Git → https://git-scm.com/
- An Anthropic API key → https://console.anthropic.com/

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Glutarios66/AutotaggingOpenSource.git
cd AutotaggingOpenSource
```

### 2. Setup and Installation

The project is designed to run within a Docker environment, simplifying dependency management.

### Prerequisites

  * **Docker & Docker Compose:** You must have Docker and Docker Compose (or the `docker compose` plugin) installed. The `setup.sh` script can install this on Debian-based systems.
  * **Python 3.11+:** Required for running the management scripts on your local machine. The `setup.sh` script can install a compatible version.
  * **Bash Shell:** Required for the setup script.

### Automated Setup (`setup.sh`)

The `setup.sh` script is designed for **Debian-based systems (like Ubuntu)** and automates the entire setup process.

**Warning:** This script requires `sudo` privileges to install system packages like Python, Git, and Docker, and it will add the current user to the `docker` group. Please review the script before running it.

1.  **Make the script executable:**
    ```bash
    chmod +x setup.sh
    ```
2.  **Run with sudo:**
    ```bash
    sudo ./setup.sh
    ```
3.  **Log Out and Log Back In:** For the `docker` group changes to take effect, you must log out of your system and log back in. Alternatively, you can run `newgrp docker` in your terminal.

### Manual Setup

If you are not on a Debian-based system or prefer a manual setup:

1.  **Install Docker and Docker Compose:** Follow the official installation guide for your operating system.
2.  **Install Python 3.11+:** Install a compatible Python version.
3.  **Create a Virtual Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

Before running the simulation, you must provide your AI API key.

1.  **Create the `.env` file:** In the project root, create a file named `.env`.
2.  **Add your API key:** Add the following line to the `.env` file, replacing the placeholder with your actual key:
    ```
    AI_API_KEY='YOUR_AI_API_KEY'
    ```

-----

## Starting the server

```bash
uvicorn main:app --reload
```

The `--reload` flag automatically restarts the server when code changes are detected — useful during development.

The server is now running at:

```
http://localhost:8000
```

---

## Testing the API

### Swagger UI (recommended)

FastAPI automatically generates interactive documentation. Open in your browser:

```
http://localhost:8000/docs
```

You can try out all endpoints directly, upload files, and inspect responses — no additional tools required.

### Health check

Verify the server is running:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### Process a document

```bash
curl -X POST http://localhost:8000/process \
  -F "file=@document.pdf" \
  -F "generate_report=true" \
  -F "shift_headings=false" \
  -F "wcag_level=AA"
```

Expected response:
```json
{
  "status": "received",
  "filename": "document.pdf",
  "tagged_pdf_url": null,
  "report": {
    "wcag_score": 0,
    "wcag_level": "AA",
    "violations_found": 0,
    "violations_fixed": 0,
    "violations": [],
    "processors_applied": [],
    "processing_time_ms": 12
  },
  "message": "File received. Processing pipeline coming soon."
}
```

---

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `file` | file | — | PDF (max. 100 MB) |
| `generate_report` | boolean | `false` | Generates a detailed WCAG audit report |
| `shift_headings` | boolean | `false` | Shifts all headings one level down (H1→H2, H2→H3, etc.) |
| `wcag_level` | string | `AA` | Conformance level to check against: `A`, `AA`, or `AAA` |

---

## Supported formats

- PDF (`.pdf`)
- Word Document (`.docx`)

---

## Response status codes

| Status | Meaning |
|---|---|
| `received` | File successfully received |
| `processing` | Currently being processed |
| `done` | Processing complete, tagged document available |
| `error` | An error occurred, see `message` for details |

---

## Project structure

```
autotagginopensource/
├── main.py                  # Entry point, FastAPI app
├── requirements.txt         # Python dependencies
├── .env                     # API keys (not committed to Git)
├── .env.example             # Template for .env
├── .gitignore
├── README.md
├── api/
│   ├── routes.py            # Endpoints: /process, /download, /health
│   └── models.py            # Request/Response schemas
├── parser/
│   └── document.py          # PDF/DOCX → Unified IR
├── processors/
│   ├── base.py              # Base interface for all processors
│   ├── alt_text.py          # Images → Alt-text via LLM
│   ├── structure.py         # Headings, reading order, tables
│   └── language.py          # Language simplification via LLM
├── checker/
│   └── wcag.py              # WCAG score and audit report
└── renderer/
    └── document.py          # Unified IR → PDF/DOCX output
```

---

## Roadmap

- [x] Phase 1 — API foundation, endpoints, validation
- [ ] Phase 2 — PDF/DOCX parser and Unified IR
- [ ] Phase 3 — Alt-text generator, structure processor
- [ ] Phase 4 — WCAG checker, report generation, Docker

---

## License

MIT License — free to use, modify, and distribute.