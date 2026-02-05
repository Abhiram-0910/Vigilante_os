# /app/services/simulator.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import SETTINGS
# Import your fast_llm instance here (or pass it in)

async def simulate_reaction(agent_draft: str, scam_type: str, llm) -> dict:
    """
    Mental Sandbox: Simulates how the scammer will react to our draft.
    Returns: Predicted Reaction + Success Probability.
    """
    prompt = ChatPromptTemplate.from_template("""
    Roleplay as a {scam_type} scammer.
    The victim says: "{draft}"
    
    1. How do you react? (Angry / Confused / Happy / Quit)
    2. What do you say next?
    
    Return format: REACTION: [State] || NEXT: [Message]
    """)
    
    try:
        chain = prompt | llm | StrOutputParser()
        result = await chain.ainvoke({"scam_type": scam_type, "draft": agent_draft})
        
        reaction, next_msg = result.split("||", 1)
        return {
            "predicted_reaction": reaction.replace("REACTION:", "").strip(),
            "predicted_next_msg": next_msg.replace("NEXT:", "").strip()
        }
    except:
        return {"predicted_reaction": "Unknown", "predicted_next_msg": "..."}