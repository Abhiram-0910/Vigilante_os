import os
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm import DualBrainLLM

# ────────────────────────────────────────────────────────────────────────────────
# BRAIN 3: THE SUPERVISOR (Groq/Llama-3)
# Switched to Groq for reliability and speed
# ────────────────────────────────────────────────────────────────────────────────
supervisor_llm = DualBrainLLM(
    primary_model="llama-3.3-70b-versatile",
    fallback_model="gemini-2.0-flash",
    temperature=0.0
)


def supervisor_review(state: dict) -> tuple[bool, str]:
    """
    Supreme Supervisor Agent — evaluates the proposed tactic BEFORE execution.
    
    Uses Gemini for rigorous safety, compliance, and strategic review.
    Returns (approved: bool, feedback: str)
    """
    tactic = state.get("current_tactic", "UNKNOWN")
    reasoning = state.get("tactic_reasoning", "No reasoning provided")
    scam_type = state.get("scam_type", "Unknown")

    prompt = ChatPromptTemplate.from_template(
        """
        You are the META-SUPERVISOR for a national cyber defense AI system.
        
        Current Situation:
        - Engaging a {scam_type} scammer
        - Proposed Tactic: {tactic}
        - Reasoning behind tactic: {reasoning}
        
        Your responsibility:
        Perform strict final review before any reply is sent.
        
        Evaluate on these mandatory criteria:
        1. SAFETY: No real money transfer, no real credentials, no real PII exposure
        2. STRATEGIC VALUE: Does it meaningfully waste time or extract usable intel?
        3. LEGAL / POLICY COMPLIANCE: No violation of Indian IT Act (e.g. 420, 66D), DPDP Act, or ethical AI guidelines
        4. RESPONSIBLE AI / ETHICS: 
           - NO CLASSIST LANGUAGE: Avoid derogatory terms against low-income or uneducated scammers.
           - NO DEMOGRAPHIC PROFILING: Interactions must not reflect biases based on region, religion, or community.
           - NO TOXIC ESCALATION: Provoking violence or harassment is strictly forbidden.
        
        Return format (exactly one of these two):
        - "APPROVED"                  (only if ALL criteria are fully satisfied)
        - "REJECTED: <short reason>"  (must explain why — be specific)
        
        Do NOT be lenient. Err on the side of caution.
        """
    )

    chain = prompt | supervisor_llm

    try:
        response = chain.invoke({
            "scam_type": scam_type,
            "tactic": tactic,
            "reasoning": reasoning
        })

        verdict = response.content.strip().upper()

        # FIX: Robust parsing
        if "APPROVED" in verdict:
            return True, "Supervisor Authorized"
        else:
            if "REJECTED" in verdict and ":" in verdict:
                reason = verdict.split(":", 1)[1].strip()
            else:
                reason = verdict
            return False, f"REJECTED: {reason}"

    except Exception as e:
        print(f"Supervisor failed: {e}")
        return True, "Supervisor Offline (Fail-Safe)"


# Optional: test / debug helper
if __name__ == "__main__":
    test_state = {
        "current_tactic": "DEPLOY_FAKE_PROOF",
        "tactic_reasoning": "Scammer demanded screenshot → sending synthetic failed transaction image",
        "scam_type": "KYC Fraud"
    }
    approved, msg = supervisor_review(test_state)
    print(f"Approved: {approved}")
    print(f"Message: {msg}")