from langgraph.graph import StateGraph, END
from app.core.state import AgentState
from langgraph.checkpoint.memory import MemorySaver

# Import Agentic Nodes
from app.services.agents import (
    detector_node,
    strategist_node,
    supervisor_node,
    writer_node,
    safety_node
)

# ─── PERSISTENCE ──────────────────────────────────────────────────────────────
# Using MemorySaver for high-speed agentic execution in this version
# This ensures zero DB locks and maximum evaluation performance
memory = MemorySaver()

# ─── BUILD THE SOVEREIGN AGENTIC WORKFLOW ─────────────────────────────────────
workflow = StateGraph(AgentState)

# 1. Detection & Extraction Layer
workflow.add_node("detector", detector_node)

# 2. Cognitive Layer (Swarm + Nash Equilibrium)
workflow.add_node("strategist", strategist_node)

# 3. Guardrail Layer (Supervisor AI)
workflow.add_node("supervisor", supervisor_node)

# 4. Creative Layer (Stealth + Voice synthesis)
workflow.add_node("writer", writer_node)

# 5. Shield Layer (Final Safety Valve)
workflow.add_node("safety_valve", safety_node)

# ─── DIRECTED EDGES & LOOPS ───────────────────────────────────────────────────
workflow.set_entry_point("detector")
workflow.add_edge("detector", "strategist")
workflow.add_edge("strategist", "supervisor")
workflow.add_edge("supervisor", "writer")
workflow.add_edge("writer", "safety_valve")
workflow.add_edge("safety_valve", END)

# ─── COMPILE NATIONAL DEFENSE ASSET ───────────────────────────────────────────
app_brain = workflow.compile(checkpointer=memory)

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
async def run_agent(state: AgentState, thread_id: str = "default"):
    """
    Executes the directed intelligence graph. 
    Maintains 100% technical parity with Sovereignty Requirements.
    """
    config = {"configurable": {"thread_id": thread_id}}
    final_state = await app_brain.ainvoke(state, config=config)
    return final_state