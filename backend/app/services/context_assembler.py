import logging
from typing import List
from app.schemas.retrieval import RetrievedItem

logger = logging.getLogger("script_supervisor.context_assembler")

def assemble_reasoning_prompt_context(items: List[RetrievedItem], scene_text: str, scene_number: int) -> str:
    """
    Context Assembler:
    Formats hybrid retrieved evidence into a structured, token-efficient,
    provenance-tagged context string for Gemini AI reasoning prompts.
    """
    lines = [f"--- ACTIVE SCENE #{scene_number} ---", "<UNTRUSTED_SCREENPLAY_CONTENT>", scene_text.strip(), "</UNTRUSTED_SCREENPLAY_CONTENT>", ""]

    facts = [i for i in items if i.item_type == "FACT"]
    events = [i for i in items if i.item_type == "EVENT"]
    knowledge = [i for i in items if i.item_type == "KNOWLEDGE"]
    writer_decisions = [i for i in items if i.item_type == "WRITER_DECISION"]
    research_items = [i for i in items if i.item_type == "RESEARCH"]
    scenes = [i for i in items if i.item_type == "SCENE"]

    if writer_decisions:
        lines.append("--- PREVIOUS WRITER REVIEW DECISIONS (AUTHORITATIVE INTENT) ---")
        for wd in writer_decisions:
            lines.append(f"{wd.provenance_tag} {wd.content}")
        lines.append("")

    if facts:
        lines.append("--- RELEVANT ESTABLISHED STORY FACTS ---")
        for f in facts:
            lines.append(f"{f.provenance_tag} {f.content}")
        lines.append("")

    if knowledge:
        lines.append("--- RELEVANT CHARACTER KNOWLEDGE STATES ---")
        for k in knowledge:
            lines.append(f"{k.provenance_tag} {k.content}")
        lines.append("")

    if events:
        lines.append("--- RELEVANT PRECEDING EVENTS ---")
        for ev in events:
            lines.append(f"{ev.provenance_tag} {ev.content}")
        lines.append("")

    if research_items:
        lines.append("--- RELEVANT PARALLEL EXTERNAL RESEARCH EVIDENCE ---")
        lines.append("<UNTRUSTED_RESEARCH_EVIDENCE>")
        for r in research_items:
            lines.append(f"{r.provenance_tag} {r.content}")
        lines.append("</UNTRUSTED_RESEARCH_EVIDENCE>")
        lines.append("")

    if scenes:
        lines.append("--- LONG-RANGE RELEVANT PREVIOUS SCENES ---")
        for sc in scenes:
            lines.append(f"{sc.provenance_tag}\n{sc.content}")
        lines.append("")

    assembled = "\n".join(lines)
    logger.info(f"Assembled reasoning context with {len(items)} items ({len(assembled)} chars).")
    return assembled
