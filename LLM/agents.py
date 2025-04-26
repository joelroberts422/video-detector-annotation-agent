import os
from dotenv import load_dotenv, find_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents.react.agent import create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import tool

load_dotenv(find_dotenv())
api_key = os.getenv("OPENAI_API_KEY")

template = """
Role and Context:

Who You Are:
You are a Traffic video annotator for Team Fast Five.

You will detect traffic anomalies with users help improving bounding boxes, traffic / pedestrian detection.

What does it mean to improve bounding boxes?
- Fill gaps where detection was lost and then was 'detected' again.
- Remove duplicate overlapping bounding boxes.
- Correct labels when, for instance, a car label switched to a truck.

Tasks:
- ADD: bounding boxes/labels where needed.
- UPDATE: labels or boxes that are incorrect.
- DELETE: duplicate detections.

Overall Goal:
Enhance video annotation accuracy. Ask for more details if unsure.
Answer the question as best you can. You have access to the following tools:

{tools}

Use this format:
Question: {question}
Thought: {agent_scratchpad}
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (Thought/Action/Action Input/Observation can repeat)
Final Answer: the final answer to the original question
"""

llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.7,
    openai_api_key=api_key,
)

prompt = PromptTemplate.from_template(template)

@tool("get", return_direct=True)
def get_tool(resource: str) -> str:
    """Retrieve annotation data for a given resource."""
    # TODO: implement actual retrieval logic
    return f"Data for {resource}"

@tool("update")
def update_tool(resource: str, changes: dict) -> str:
    """Apply updates to annotation data."""
    # TODO: implement update logic
    return "updated"

@tool("delete")
def delete_tool(resource: str) -> str:
    """Remove annotation entries."""
    # TODO: implement delete logic
    return "deleted"

@tool("undo")
def undo_tool(action_id: str) -> str:
    """Revert a previous annotation action."""
    # TODO: implement undo logic
    return "undone"

annotation_agent = create_react_agent(   
    llm=llm,
    tools=[get_tool, update_tool, delete_tool, undo_tool],
    prompt=prompt,)

chain = prompt | annotation_agent

def annotate_with_agent(question: str) -> str:
    return annotation_agent.invoke({"question": question})

# while True:
#     print("\n\n-------------------------------")
#     question = input("Ask your question (q to quit): ")
#     print("\n\n")
#     if question == "q":
#         break
    
#     result = chain.invoke({"question": question})
#     print(result)