"""Window quote chatbot v2: router, window expert, config generator (parser), support agent."""

import yaml
from enum import Enum
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from llm_io.model_io import ModelIO
from project_quoter.window_description_parser import WindowDescriptionParser


class Node(Enum):
    """Graph node names; use for next (routing) and prev (last node that ran)."""
    ROUTER = "router"
    WINDOW_EXPERT = "window_expert"
    DIRECT_WINDOW_EXPERT = "direct_window_expert"
    GENERATOR = "generator"
    SUPPORT_AGENT = "support_agent"


# State: messages are list of BaseMessage; next/prev set by router and nodes.
class State(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    next: Node
    prev: Node

llm = ChatOpenAI(model="gpt-4o-mini")
model_io = ModelIO(llm=llm)


def router(state: State):
    """Classify the last turn: route to window_expert, direct_window_expert, or generator."""
    print("[node] router")
    system_prompt = (
        "You are a message classifier for a window quoting system. "
        "Route to 'question' if the user is asking about windows (info, advice). "
        "Route to 'direct' if the user has a short factual window question. "
        "Route to 'project_info' if they are giving project details (dimensions, type, etc.). "
        "Reply with only one word: question, direct, or project_info."
    )
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    out = model_io.get_response(messages_lc=messages)
    classification = (getattr(out, "content", out) or "").strip().lower()
    if "direct" in classification:
        next_node = Node.DIRECT_WINDOW_EXPERT
    elif "question" in classification:
        next_node = Node.WINDOW_EXPERT
    else:
        next_node = Node.GENERATOR
    return {"next": next_node, "prev": Node.ROUTER}


def window_expert(state: State):
    """Answer window-related questions using the last user message; returns one assistant message."""
    print("[node] window_expert")
    print(state["messages"])
    last_user = next((m for m in reversed(state["messages"]) if getattr(m, "type", None) == "human"), None)
    content = last_user.content if last_user else ""
    system_prompt = (
        "You are a window expert with deep knowledge about window types, materials, energy efficiency, "
        "and installation. Provide accurate, helpful information about windows based on the user's question. "
        "Be informative but concise. Focus only on providing factual information about windows."
    )
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=content)]
    out = model_io.get_response(messages_lc=messages)
    if not out:
        out = AIMessage(content="I couldn't answer that; please try again.")
    return {"messages": [out], "prev": Node.WINDOW_EXPERT}


def direct_window_expert(state: State):
    """Answer window questions using full conversation; then to support_agent."""
    print("[node] direct_window_expert")
    system_prompt = (
        "You are a window expert. Answer the user's window-related question using the full conversation for context. "
        "Be concise and factual."
    )
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    out = model_io.get_response(messages_lc=messages)
    if not out:
        out = AIMessage(content="I couldn't answer that; please try again.")
    return {"messages": [out], "prev": Node.DIRECT_WINDOW_EXPERT}


def config_generator(state: State):
    """Turn conversation into window descriptions (YAML) via WindowDescriptionParser; append assistant message or ask for more info."""
    print("[node] config_generator")
    parser_io = ModelIO(prompt=WindowDescriptionParser.prompt_instructions, llm=llm)
    parser = WindowDescriptionParser(parser_io, debug=False)
    config = parser.generate_window_descriptions(state["messages"])

    if config:
        yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)
        return {"messages": [AIMessage(content=yaml_str)], "prev": Node.GENERATOR}
    return {"messages": [AIMessage(content="I couldn't parse that into window descriptions. Can you share the window sizes and types (e.g. quantity, width, height, and a short description for each)?")], "prev": Node.GENERATOR}


def support_agent(state: State):
    """Act based on prev: if window_expert, format reply and offer follow-ups; if generator, placeholder."""
    print("[node] support_agent")
    prev = state.get("prev")
    if prev in (Node.WINDOW_EXPERT, Node.DIRECT_WINDOW_EXPERT):
        system_prompt = (
            "You are the customer-facing window-quote assistant. Your role is to properly format responses and prompt for project information. "
            "The last message in the conversation is the assistant's answer to a window question. Rewrite it to be clear and well-formatted. "
            "Then add one short sentence offering to answer more questions and prompt for info on their project (e.g. height, width, quantity, window type) so that we can provide them a price range. "
            "Keep the tone concise and helpful."
        )
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        out = model_io.get_response(messages_lc=messages)
        return {"messages": [out], "prev": Node.SUPPORT_AGENT} if out else {"prev": Node.SUPPORT_AGENT}
    if prev == Node.GENERATOR:
        return {"messages": [AIMessage(content="Received.")], "prev": Node.SUPPORT_AGENT}
    return {"prev": Node.SUPPORT_AGENT}


builder = StateGraph(State)
builder.add_node("router", router)
builder.add_node("window_expert", window_expert)
builder.add_node("direct_window_expert", direct_window_expert)
builder.add_node("generator", config_generator)
builder.add_node("support_agent", support_agent)
builder.add_edge(START, "router")
builder.add_conditional_edges(
    "router",
    lambda x: x["next"],
    {
        Node.WINDOW_EXPERT: "window_expert",
        Node.DIRECT_WINDOW_EXPERT: "direct_window_expert",
        Node.GENERATOR: "generator",
    },
)
builder.add_edge("window_expert", "support_agent")
builder.add_edge("direct_window_expert", "support_agent")
builder.add_edge("generator", "support_agent")
builder.add_edge("support_agent", END)

agent_app = builder.compile(checkpointer=MemorySaver())


def run_cli():
    print("AI quote estimator bot:")
    config = {"configurable": {"thread_id": "unique_user_id_123"}}
    current_state = {"messages": []}
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        current_state["messages"].append(HumanMessage(content=user_input))
        current_state = agent_app.invoke(current_state, config=config)
        last = current_state["messages"][-1]
        print(f"Agent: {last.content}")


if __name__ == "__main__":
    run_cli()
