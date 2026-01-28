from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from dissertation.core.exporter import export_bundle
from dissertation.core.orchestrator import run_agentic, run_llm_baseline
from dissertation.models.schemas import Epic

st.set_page_config(page_title="Agentic Requirements Generator", layout="wide")
st.title("Agentic Requirements Generator")
st.caption("Enter an Epic → Generate User Stories + Gherkin + Traceability + Audit trail")

with st.sidebar:
    st.header("Run settings")
    mode = st.selectbox("Mode", ["llm_baseline", "agentic"], index=1)
    model = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)

    if mode == "llm_baseline":
        use_openai = st.checkbox("Use OpenAI", value=True)
    else:
        force_min_iters = st.number_input(
            "Force min iters", min_value=0, max_value=5, value=1, step=1
        )
        max_iters = st.number_input("Max iters", min_value=0, max_value=5, value=2, step=1)
        target_score = st.number_input(
            "Target score", min_value=1.0, max_value=5.0, value=4.2, step=0.1
        )

st.subheader("Epic input")
st.warning(
    "⚠️ Do not enter personal data (e.g., names, emails, phone numbers, addresses, registration plates, VINs). "
    "Use placeholders like [USER], [EMAIL], [PHONE], [ADDRESS]."
)

col1, col2 = st.columns(2)
with col1:
    epic_id = st.text_input("Epic ID", value="E-WEB-001")
with col2:
    out_dir = st.text_input("Output folder", value="outputs")

epic_text = st.text_area(
    "Epic text", height=120, placeholder="As a <role>, I want <goal>, so that <benefit>."
)

constraints_text = st.text_area(
    "Constraints (one per line)",
    height=100,
    value="Do not expose whether an email address exists in the system.",
)

glossary_text = st.text_area(
    "Glossary (one per line: term: definition)",
    height=100,
    value="",
)

generate = st.button("🚀 Generate", type="primary")


def parse_glossary(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for line in [raw_line.strip() for raw_line in text.splitlines() if raw_line.strip()]:
        if ":" not in line:
            raise ValueError(f"Glossary line must be 'term: definition' but got: {line}")
        term, definition = [x.strip() for x in line.split(":", 1)]
        items.append({"term": term, "definition": definition})
    return items


def read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


if generate:
    try:
        if not epic_text.strip():
            raise ValueError("Epic text is required.")

        epic = Epic(
            epic_id=epic_id.strip(),
            text=epic_text.strip(),
            constraints=[c.strip() for c in constraints_text.splitlines() if c.strip()],
            glossary=parse_glossary(glossary_text),
        )

        # Set model for this run (keeps your CLI behaviour consistent)
        os.environ["OPENAI_MODEL"] = model

        if mode == "llm_baseline":
            req = run_llm_baseline(
                epic,
                force_openai=bool(use_openai),
                model_name=model,
                temperature=float(temperature),
            )
        else:
            req = run_agentic(
                epic,
                model_name=model,
                temperature=float(temperature),
                max_iters=int(max_iters),
                target_score=float(target_score),
                out_dir=str(out_dir),
                force_min_iters=int(force_min_iters),
            )

        run_folder = export_bundle(epic, req, out_dir)
        run_path = Path(run_folder)

        st.success(f"✅ Exported to: {run_folder}")

        # Preview panel
        st.subheader("requirements.md (preview)")
        st.markdown(read_text_if_exists(run_path / "requirements.md"))

        # Evidence panel
        st.subheader("Evidence (scores + audit)")
        scores = read_text_if_exists(run_path / "iteration_scores.csv")
        audit = read_text_if_exists(run_path / "audit_log.jsonl")

        c1, c2 = st.columns(2)
        with c1:
            st.caption("iteration_scores.csv")
            st.code(scores if scores else "(no iteration_scores.csv found)")
        with c2:
            st.caption("audit_log.jsonl (first 20 lines)")
            if audit:
                st.code("\n".join(audit.splitlines()[:20]))
            else:
                st.code("(no audit_log.jsonl found)")

        # Downloads
        st.subheader("Downloads")
        req_json = read_text_if_exists(run_path / "requirement_set.json")
        st.download_button(
            "Download requirement_set.json",
            req_json,
            file_name="requirement_set.json",
            mime="application/json",
        )

    except Exception as e:
        st.error(str(e))
