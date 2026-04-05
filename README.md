# Master of Science in Artificial Intelligence Dissertation — Agentic Requirements Generator

This project implements an agentic pipeline that transforms epics into user stories and Gherkin scenarios, with validation and scoring utilities.

> ⚠️ This application is part of an MSc dissertation project and is intended for research and evaluation purposes.

## Live Demo
Access the deployed application here:  
https://agentic-requirements-generator.streamlit.app

---

## Overview

The system uses a multi-agent architecture consisting of:
- **Generator Agent** – produces initial requirements
- **Critic Agent** – evaluates quality and consistency
- **Refiner Agent** – improves outputs based on feedback
- **Baseline Model** – provides comparison outputs

The pipeline supports:
- User story generation  
- Gherkin scenario creation  
- Traceability and validation  
- Iterative refinement  

---

## Technology Stack
* Python 3.11
* Streamlit (web UI)
* PostgreSQL (Neon, serverless) + pgvector  
* SQLAlchemy
* OpenAI API

--

## Deployment

The system is deployed as a web application using:

- **Frontend/UI**: Streamlit Cloud  
- **Backend**: Python (agentic pipeline)  
- **Database**: PostgreSQL (Neon)  
- **Vector Support**: pgvector extension  

--

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

dissertation --help


### Add `LICENSE` (MIT)
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
