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

# --- STEP 1: State ---
class State(TypedDict):
    messages: Annotated[list, add_messages]
    config: Optional[dict]
    warnings: Optional[list]
    config_valid: bool

llm = ChatOpenAI(model="gpt-4o-mini")
# llm_with_tools = llm.bind_tools(tools)

def config_generator(state: State):
    # Review message history and generate config
    last_msgs = state['messages']
    system_prompt = generate_prompt(last_msgs)
    # print(system_prompt)
    response = llm.invoke(system_prompt)
    return {"messages": [response]}

def config_validator(state: State):
    last_response = state["messages"][-1].content
    # print(last_response)
    config = yaml.safe_load(last_response)

    generator = ValidConfigGenerator("gpt-4.1", debug = True)
    errs, warnings = generator.validate_config(config)

    if not errs:
        return {"config" : config, "config_valid" : True}
    else:
        return {"warnings": warnings}
    
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

builder.add_node("assistant", support_agent)
builder.add_node("validator", config_validator)
builder.add_node("generator", config_generator)
# builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "generator")
builder.add_edge("generator", "validator")
builder.add_edge("validator", "assistant")
builder.add_edge("assistant", END)
memory = MemorySaver()
agent_app = builder.compile(checkpointer=memory)


def run_cli():
    print("AI quote estimator bot:")
    current_state = {"messages": [], "config": None, "config_valid": False}
    
    while True:
        if current_state.get("config_valid"):
            print(f"✅ Success! We have a quote.")
            break

        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]: break
        
                # Add user message to state
        current_state["messages"].append(("user", user_input))
        
        # Run graph
        current_state = agent_app.invoke(current_state)
        
        # Print Assistant response
        print(f"Agent: {current_state['messages'][-1].content}")


if __name__ == "__main__":
    run_cli()
