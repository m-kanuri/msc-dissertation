# Master of Science in Artificial Intelligence Dissertation — Agentic Requirements Generator

This project implements an agentic pipeline that transforms epics into user stories and Gherkin scenarios, with validation and scoring utilities.
## Technology Stack
* Python 3.11
* Streamlit (web UI)
* PostgreSQL 16 + pgvector
* SQLAlchemy
* OpenAI API
## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

dissertation --help


### D) Add `LICENSE` (MIT)
```bash
cat > LICENSE <<'EOF'
MIT License

Copyright (c) 2026 Murthy Kanuri

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
