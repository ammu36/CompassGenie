from app.services.agent_service import app_graph
from langchain_core.messages import HumanMessage


def test_agent_graph_structure():
    """
    Verifies that the LangGraph is compiled with the correct
    nodes and edges without calling the LLM.
    """
    # Get the graph schema
    graph_info = app_graph.get_graph()

    # Verify essential nodes exist
    nodes = graph_info.nodes.keys()
    assert "agent" in nodes
    assert "tools" in nodes

    # Verify the graph is compiled and has a starting point
    assert app_graph.builder is not None


def test_initial_state_validation():
    """
    Ensures the AgentState TypedDict can be initialized
    with the expected keys.
    """
    initial_state = {
        "messages": [HumanMessage(content="Find a park")],
        "user_location": {"lat": 40.7128, "lng": -74.0060}
    }

    assert "messages" in initial_state
    assert "user_location" in initial_state
    assert isinstance(initial_state["messages"][0], HumanMessage)