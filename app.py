import json
import textwrap
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="AI Use Case Builder", page_icon="🤖", layout="wide")


SYSTEM_GUIDANCE = """
You are helping draft a practical internal AI use case card.
Your job is to transform rough user inputs into a structured, plain-language use case.

Rules:
- Be concrete and practical.
- Do not overhype AI.
- Prefer narrow, testable use cases over broad transformation language.
- Call out data sensitivity, operational risk, and feasibility concerns.
- If the idea is weak, say so professionally.
- Recommend one of: Reject, Refine, Pilot.
- Do not mention model names, vendors, or technical architecture unless the user explicitly provided them.
""".strip()


QUESTION_HELP = {
    "problem": "What is the real business or operational problem?",
    "users": "Who experiences this problem or would use the solution?",
    "current_process": "How is the work done today?",
    "pain_points": "What is slow, manual, inconsistent, or frustrating?",
    "ai_role": "What part might AI help with?",
    "systems": "What systems, documents, or data sources are involved?",
    "sensitive_data": "Would this involve member data, account data, operationally sensitive data, or other restricted information?",
    "expected_value": "What improvement would matter: time saved, fewer errors, faster triage, consistency, better service, etc.?",
    "human_review": "Where must a human stay in the loop?",
    "constraints": "What constraints matter: closed environment, no external data sharing, licensing, approvals, staff time, etc.?",
}


OUTPUT_TEMPLATE = """
# AI Use Case Card

**Title**  
{title}

**Problem Statement**  
{problem_statement}

**Who Is Affected**  
{who_is_affected}

**Current Process**  
{current_process}

**Pain Points**  
{pain_points}

**Potential AI Role**  
{ai_role}

**Potential Value**  
{potential_value}

**Systems or Inputs Involved**  
{systems_inputs}

**Data Sensitivity / Governance Notes**  
{data_notes}

**Human Oversight Needed**  
{human_review}

**Constraints / Dependencies**  
{constraints}

**Feasibility Assessment**  
{feasibility}

**Recommended Next Step**  
{recommendation}

**Suggested Pilot Approach**  
{pilot}
""".strip()


def clean_line(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "Not provided."
    return " ".join(value.split())



def infer_title(problem: str, ai_role: str) -> str:
    problem = clean_line(problem)
    ai_role = clean_line(ai_role)
    if problem != "Not provided.":
        base = problem[:70].rstrip(" .")
        return f"AI assist for {base[0].lower() + base[1:] if len(base) > 1 else base.lower()}"
    if ai_role != "Not provided.":
        base = ai_role[:70].rstrip(" .")
        return f"AI use case for {base[0].lower() + base[1:] if len(base) > 1 else base.lower()}"
    return "Untitled AI use case"



def assess_sensitivity(sensitive_data: str, systems: str, constraints: str) -> str:
    text = " ".join([sensitive_data.lower(), systems.lower(), constraints.lower()])
    flagged_terms = [
        "member",
        "account",
        "customer",
        "pii",
        "personally identifiable",
        "operational",
        "ot",
        "cyber",
        "restricted",
        "confidential",
        "proprietary",
    ]
    if any(term in text for term in flagged_terms):
        return (
            "This use case appears to involve potentially sensitive or restricted information. "
            "Any prototype should minimize data exposure, avoid external sharing unless explicitly approved, "
            "and define clear governance boundaries before testing."
        )
    if clean_line(sensitive_data) == "Not provided.":
        return "Data sensitivity was not clearly defined. Confirm data classes and sharing restrictions before proceeding."
    return "No obvious sensitive-data issue was described, but governance should still be checked before implementation."



def assess_feasibility(ai_role: str, systems: str, constraints: str, sensitive_data: str) -> str:
    combined = " ".join([ai_role.lower(), systems.lower(), constraints.lower(), sensitive_data.lower()])
    hard_terms = ["production", "real-time", "autonomous", "directly query", "write back", "member data", "account"]
    medium_terms = ["multiple systems", "integration", "api", "approval", "security", "licensing"]

    if any(term in combined for term in hard_terms):
        return (
            "Moderate to difficult. This idea likely requires stronger controls, more technical integration, "
            "or tighter governance than a simple pilot. A narrow, low-risk first step would be important."
        )
    if any(term in combined for term in medium_terms):
        return (
            "Moderate. The use case looks plausible, but dependencies such as systems access, approvals, or workflow design "
            "may affect how quickly it can be piloted."
        )
    return "Reasonable for a first pilot, especially if kept narrow and limited to low-risk inputs."



def recommend_next_step(problem: str, ai_role: str, expected_value: str, constraints: str, sensitive_data: str) -> str:
    missing_core = sum(
        1
        for item in [problem, ai_role, expected_value]
        if clean_line(item) == "Not provided."
    )
    combined = " ".join([constraints.lower(), sensitive_data.lower(), ai_role.lower()])

    if missing_core >= 2:
        return "Refine. The idea needs a clearer problem statement, AI role, and expected value before it is ready for review."
    if "member" in combined or "account" in combined or "external" in combined:
        return "Refine. Clarify governance, data boundaries, and a low-risk pilot design before moving ahead."
    if clean_line(problem) != "Not provided." and clean_line(ai_role) != "Not provided.":
        return "Pilot. Define a small, low-risk test with clear success criteria and human review."
    return "Reject or Refine depending on business importance. The concept is still too vague to justify action."



def suggest_pilot(problem: str, ai_role: str, sensitive_data: str) -> str:
    combined = " ".join([problem.lower(), ai_role.lower(), sensitive_data.lower()])
    if "sensitive" in combined or "member" in combined or "account" in combined:
        return (
            "Start with synthetic, redacted, or non-sensitive examples only. Keep a human in the loop, "
            "do not connect directly to production systems, and measure whether the tool improves clarity, speed, or consistency."
        )
    return (
        "Start with a narrow workflow, a small set of users, and a fixed evaluation period. "
        "Measure time saved, reduction in back-and-forth, consistency of output, and user usefulness."
    )



def build_card(inputs: dict) -> str:
    title = infer_title(inputs["problem"], inputs["ai_role"])
    return OUTPUT_TEMPLATE.format(
        title=title,
        problem_statement=clean_line(inputs["problem"]),
        who_is_affected=clean_line(inputs["users"]),
        current_process=clean_line(inputs["current_process"]),
        pain_points=clean_line(inputs["pain_points"]),
        ai_role=clean_line(inputs["ai_role"]),
        potential_value=clean_line(inputs["expected_value"]),
        systems_inputs=clean_line(inputs["systems"]),
        data_notes=assess_sensitivity(inputs["sensitive_data"], inputs["systems"], inputs["constraints"]),
        human_review=clean_line(inputs["human_review"]),
        constraints=clean_line(inputs["constraints"]),
        feasibility=assess_feasibility(
            inputs["ai_role"], inputs["systems"], inputs["constraints"], inputs["sensitive_data"]
        ),
        recommendation=recommend_next_step(
            inputs["problem"], inputs["ai_role"], inputs["expected_value"], inputs["constraints"], inputs["sensitive_data"]
        ),
        pilot=suggest_pilot(inputs["problem"], inputs["ai_role"], inputs["sensitive_data"]),
    )



def build_json_payload(inputs: dict) -> str:
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_guidance": SYSTEM_GUIDANCE,
        "inputs": inputs,
        "card_markdown": build_card(inputs),
    }
    return json.dumps(payload, indent=2)


st.title("🤖 AI Use Case Builder")
st.caption("Turn a rough idea into a structured AI use-case card.")

with st.expander("What this tool is for", expanded=True):
    st.markdown(
        textwrap.dedent(
            """
            Use this to take a rough AI idea and shape it into something reviewable.

            Good for:
            - clarifying the problem
            - identifying value and constraints
            - flagging governance concerns
            - recommending whether to reject, refine, or pilot

            Avoid entering sensitive data such as member IDs, account numbers, or confidential operational details.
            """
        ).strip()
    )

left, right = st.columns([1.1, 1.0])

with left:
    st.subheader("Input")
    with st.form("use_case_form"):
        problem = st.text_area(QUESTION_HELP["problem"], height=110)
        users = st.text_input(QUESTION_HELP["users"])
        current_process = st.text_area(QUESTION_HELP["current_process"], height=90)
        pain_points = st.text_area(QUESTION_HELP["pain_points"], height=90)
        ai_role = st.text_area(QUESTION_HELP["ai_role"], height=90)
        systems = st.text_area(QUESTION_HELP["systems"], height=80)
        sensitive_data = st.text_area(QUESTION_HELP["sensitive_data"], height=80)
        expected_value = st.text_area(QUESTION_HELP["expected_value"], height=80)
        human_review = st.text_area(QUESTION_HELP["human_review"], height=80)
        constraints = st.text_area(QUESTION_HELP["constraints"], height=80)

        submitted = st.form_submit_button("Generate Use Case Card")

inputs = {
    "problem": problem if "problem" in locals() else "",
    "users": users if "users" in locals() else "",
    "current_process": current_process if "current_process" in locals() else "",
    "pain_points": pain_points if "pain_points" in locals() else "",
    "ai_role": ai_role if "ai_role" in locals() else "",
    "systems": systems if "systems" in locals() else "",
    "sensitive_data": sensitive_data if "sensitive_data" in locals() else "",
    "expected_value": expected_value if "expected_value" in locals() else "",
    "human_review": human_review if "human_review" in locals() else "",
    "constraints": constraints if "constraints" in locals() else "",
}

with right:
    st.subheader("Output")
    if submitted:
        card = build_card(inputs)
        st.markdown(card)

        st.download_button(
            label="Download card as Markdown",
            data=card,
            file_name="ai_use_case_card.md",
            mime="text/markdown",
        )

        st.download_button(
            label="Download full payload as JSON",
            data=build_json_payload(inputs),
            file_name="ai_use_case_payload.json",
            mime="application/json",
        )
    else:
        st.info("Fill in the form on the left, then generate the use-case card.")

st.divider()
with st.expander("Starter example"):
    st.markdown(
        textwrap.dedent(
            """
            **Problem:** Staff bring rough AI ideas, but they vary widely in quality and are hard to compare.

            **Users:** IT and business leaders proposing AI opportunities.

            **Current process:** Ideas are discussed informally in meetings or email.

            **Pain points:** Ideas are vague, not easy to compare, and often miss value, constraints, or risk.

            **Potential AI role:** Help structure rough ideas into a standard use-case card.

            **Systems/data involved:** Internal forms or a lightweight app. No sensitive business data required for the first version.

            **Sensitive data concerns:** Avoid member or account data entirely.

            **Expected value:** Better idea quality, faster evaluation, and a more credible AI opportunity pipeline.

            **Human review:** A person should review the generated card before any decision or sharing.

            **Constraints:** Closed environment, limited tooling, and need for practical low-risk pilots.
            """
        ).strip()
    )
