"""
Pocket Flow definition for the Spec Interviewer.
Using AsyncFlow for NiceGUI compatibility.
"""

from pocketflow import AsyncFlow
from .nodes import ChatInputNode, LLMEvaluateNode, GenerateSpecNode


def create_spec_interviewer_flow():
    """
    Create and return the Spec Interviewer flow.
    
    Note: No cyclical connection - flow terminates after each LLM response
    to yield control back to NiceGUI for user input.
    """
    # Create node instances
    chat_input_node = ChatInputNode()
    llm_evaluate_node = LLMEvaluateNode()
    generate_spec_node = GenerateSpecNode()

    # Create flow connections
    # Linear flow only - no loops!
    chat_input_node - "evaluate" >> llm_evaluate_node
    llm_evaluate_node - "generate" >> generate_spec_node
    # Note: "continue" action has no successor - flow terminates gracefully

    # Create AsyncFlow
    return AsyncFlow(start=chat_input_node)
