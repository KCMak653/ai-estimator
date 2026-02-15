import json
import os
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
# from utils import tools
from langgraph.prebuilt import ToolNode
from .config_generator.config_generator_prompt import *
import yaml
from valid_config_generator.valid_config_generator import ValidConfigGenerator
from window_quoter.window_quoter import WindowQuoter
from project_quoter.window_description_parser import WindowDescriptionParser

# --- STEP 1: State ---
class State(TypedDict):
    messages: Annotated[list, add_messages]
    config: Optional[dict]
    warnings: Optional[list]
    config_valid: bool

llm = ChatOpenAI(model="gpt-4o-mini")
# llm_with_tools = llm.bind_tools(tools)

def router(state: State):
    # Determine if the user is asking for information or providing config details
    last_user_message = next((msg.content for msg in reversed(state['messages']) 
                             if hasattr(msg, 'role') and msg.role == "user"), "")
    
    # Use LLM to classify the message
    system_prompt = (
        "You are a message classifier for a window quoting system. Determine if the user message is asking for information "
        "about windows (questions, explanations, etc.) or if they are providing configuration details for a window quote. "
        "Respond with ONLY one of these exact words: 'information' or 'configuration'."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Classify this message: {last_user_message}"}
    ]
    
    response = llm.invoke(messages)
    classification = response.content.strip().lower()
    
    # Return a dictionary with the routing decision
    return {"next": "window_expert" if "information" in classification else "generator"}

def window_expert(state: State):
    # Provide expert information about windows
    last_user_message = next((msg.content for msg in reversed(state['messages']) 
                             if hasattr(msg, 'role') and msg.role == "user"), "")
    
    system_prompt = (
        "You are a window expert with deep knowledge about window types, materials, energy efficiency, "
        "and installation. Provide accurate, helpful information about windows based on the user's question. "
        "Be informative but concise. Focus only on providing factual information about windows."
    )
    
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": last_user_message}]
    response = llm.invoke(messages)
    
    return {"messages": [response]}

def config_generator(state: State):
    # Review message history and generate config
    last_msgs = state['messages']
    system_prompt = generate_prompt(last_msgs)
    # print(system_prompt)
    response = llm.invoke(system_prompt)
    return {"messages": [response]}

def config_validator(state: State):
    last_response = state["messages"][-1].content
    
    try:
        # Parse the YAML config from the last response
        config = yaml.safe_load(last_response)
        
        # Use WindowDescriptionParser to generate window descriptions
        parser = WindowDescriptionParser(model_name="gpt-4o-mini")
        window_descriptions = parser.generate_window_descriptions(last_response)
        
        # Check if window descriptions were successfully generated
        if not window_descriptions:
            return {"config_valid": False, "warnings": ["Unable to parse window descriptions from the provided configuration."]}
        
        # Validate the generated window descriptions with ValidConfigGenerator
        generator = ValidConfigGenerator("gpt-4.1", debug=True)
        errs, warnings = generator.validate_config(config)
        
        if not errs:
            return {"config": config, "config_valid": True, "warnings": []}
        else:
            return {"config_valid": False, "warnings": warnings}
    except Exception as e:
        # Handle any exceptions during parsing or validation
        return {"config_valid": False, "warnings": [f"Error processing configuration: {str(e)}"]}
    
def support_agent(state: State):
    print("support_agent")
    is_valid = state.get("config_valid", False)
    if is_valid:
        pricing_config_path: str = "valid_config_generator/pricing.yaml"
        window_cost, window_breakdown = WindowQuoter(state["config"], pricing_config_path).quote_window()
        perm_message = f"The user has provided enough info for a quote to be generated. Inform them that {window_cost} is the total cost. Regurgitate the config they provided in natural language"
    else:
        perm_message = f"The user has not yet provided enough info to generate a config. Here are the warnings {state['warnings']}. Interpret the warnings and ask them clarifying questions"
    # print(perm_message)
    system_prompt = (
        f"You are a friendly assistant helping customers get quotes for their window projects in a chat interface. Keep your responses direct and concise while maintaining a friendly tone. Avoid unnecessary explanations or verbosity. {perm_message}")
    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": [response]}


builder = StateGraph(State)

builder.add_node("router", router)
builder.add_node("window_expert", window_expert)
builder.add_node("assistant", support_agent)
builder.add_node("validator", config_validator)
builder.add_node("generator", config_generator)
# builder.add_node("tools", ToolNode(tools))

# Add router as the starting point
builder.add_edge(START, "router")

# Router decides where to send the message
builder.add_conditional_edges(
    "router",
    lambda x: x["next"],
    {
        "window_expert": "window_expert",
        "generator": "generator"
    }
)

# Window expert path
builder.add_edge("window_expert", "assistant")

# Config generator path
builder.add_edge("generator", "validator")
builder.add_edge("validator", "assistant")
builder.add_edge("assistant", END)
memory = MemorySaver()
agent_app = builder.compile(checkpointer=memory)


def run_cli():
    print("AI quote estimator bot:")
    config = {"configurable": {"thread_id": "unique_user_id_123"}}
    current_state = {"messages": [], "config": None, "config_valid": False, "warnings": []}
    
    while True:
        if current_state.get("config_valid"):
            print(f"✅ Success! We have a quote.")
            break

        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]: break
        
                # Add user message to state
        current_state["messages"].append(("user", user_input))
        
        # Run graph
        current_state = agent_app.invoke(current_state, config=config)
        
        # Print Assistant response
        print(f"Agent: {current_state['messages'][-1].content}")


if __name__ == "__main__":
    run_cli()
