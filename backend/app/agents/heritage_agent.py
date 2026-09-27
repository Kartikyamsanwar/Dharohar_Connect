"""Heritage Agent — retrieves local knowledge and generates source-grounded responses."""

from app.data_loader import retrieve_heritage_knowledge, HERITAGE
from app.services.llm_service import generate_response

GUIDE_SYSTEM_PROMPT = """You are the DHAROHAR CONNECT AI Heritage Guide for Indian heritage sites.

Rules:
- Answer ONLY using the provided reference knowledge.
- Never invent historical facts, dates, or claims.
- If information is unavailable, clearly state it could not be verified.
- Be concise and understandable for travelers and students.
- Structure responses with these sections when relevant:
  **Historical significance**
  **Architectural significance**
  **Cultural significance**
  **Sources**
- Clearly distinguish verified sources from community content when mentioned.
- Keep responses under 300 words unless the user asks for detail."""


def _format_context(sites: list) -> str:
    if not sites:
        return "No matching heritage records found in the curated knowledge base."
    parts = []
    for s in sites:
        parts.append(
            f"Site: {s['name']} ({s['state']})\n"
            f"Category: {s['category']}\n"
            f"Period: {s.get('period', 'N/A')}\n"
            f"Description: {s['description']}\n"
            f"Significance: {s['significance']}\n"
            f"Verified sources: {', '.join(s.get('sources', []))}"
        )
    return "\n\n---\n\n".join(parts)


def _fallback_answer(message: str, sites: list, sources: list) -> str:
    if not sites:
        sample = ", ".join(s["name"] for s in HERITAGE[:8])
        return (
            "I could not verify information for that query in the curated heritage knowledge base. "
            f"Try asking about sites such as {sample}, and more."
        )
    site = sites[0]
    return (
        f"**Historical significance**\n{site['significance']}\n\n"
        f"**Architectural significance**\n{site['name']} is classified as {site['category']} heritage "
        f"from the {site.get('period', 'historical period')}. {site['description']}\n\n"
        f"**Cultural significance**\nThis site is part of India's living cultural landscape and "
        f"continues to inspire research, tourism and community storytelling.\n\n"
        f"**Sources**\n{', '.join(sources) if sources else 'DHAROHAR curated heritage knowledge base'}"
    )


def answer_heritage_question(message: str) -> dict:
    sites, sources = retrieve_heritage_knowledge(message)
    context = _format_context(sites)

    llm = generate_response(
        message,
        system_prompt=GUIDE_SYSTEM_PROMPT,
        context=context,
    )

    if llm["mode"] == "groq":
        return {
            "answer": llm["text"],
            "sources": sources or ["DHAROHAR curated heritage knowledge base"],
            "mode": "groq",
            "heritage_sites": [s["name"] for s in sites],
            "label": "verified" if sites else "unverified",
        }

    return {
        "answer": _fallback_answer(message, sites, sources),
        "sources": sources or ["DHAROHAR curated heritage knowledge base"],
        "mode": "local knowledge fallback",
        "heritage_sites": [s["name"] for s in sites],
        "label": "verified" if sites else "unverified",
    }


def select_heritage_for_trip(destination: str, interests: str) -> list:
    from app.data_loader import find_heritage

    selected = find_heritage(destination)
    if selected:
        return [selected]
    interest = interests.lower()
    return [
        x
        for x in HERITAGE
        if interest and interest in (x["category"] + " " + x["description"]).lower()
    ][:3]
