import os
from dotenv import load_dotenv, find_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents.react.agent import create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import tool
import pandas as pd
import uuid

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

@tool("update", return_direct=True)
def update_tool(
    filename: str,
    record_id: str,
    bbox: list[int],
    trackerId: int,
    frameId: int,
    class_id: int,
    class_name: str,
    confidence: float,
) -> bool:
    """
    Update a single annotation record in `filename` (JSON orient='records'),
    then save changes back to the same file.

    Args:
        filename: Path to the JSON file.
        record_id: The 'id' value of the record to update.
        bbox: [x1, y1, x2, y2] coordinates.
        trackerId: Tracker identifier to set.
        frameId: Frame number to set.
        class_id: New numeric class ID.
        class_name: New class name.
        confidence: New confidence score.

    Returns:
        True if the record was found and updated; False otherwise.
    """
    try:
        # Load the file as a list of records
        df = pd.read_json(filename, orient="records")
    except Exception:
        return False

    # Locate the row(s) matching record_id
    match = df["id"] == record_id
    if not match.any():
        return False

    idx = df[match].index

    # Unpack and assign bounding box coords
    x1, y1, x2, y2 = bbox
    df.loc[idx, "x1"] = x1
    df.loc[idx, "y1"] = y1
    df.loc[idx, "x2"] = x2
    df.loc[idx, "y2"] = y2

    # Update additional fields
    df.loc[idx, "trackerId"]   = trackerId
    df.loc[idx, "frameId"]     = frameId
    df.loc[idx, "class_id"]    = class_id
    df.loc[idx, "class_name"]  = class_name
    df.loc[idx, "confidence"]  = confidence

    try:
        # Save back to the same JSON file
        df.to_json(filename, orient="records", indent=2)
    except Exception:
        return False

    return True

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

@tool("add", return_direct=True)
def add_tool(
    filename: str,
    bbox: list[int],
    trackerId: int,
    frameId: int,
    class_id: int,
    class_name: str,
    confidence: float,
) -> bool:
    """
    Prepend a new annotation record to `filename` (JSON orient='records').

    Args:
        filename: Path to the JSON file.
        bbox: [x1, y1, x2, y2] coordinates.
        trackerId: Tracker identifier to set.
        frameId: Frame number to set.
        class_id: Numeric class ID.
        class_name: Human-readable class name.
        confidence: Confidence score.

    Returns:
        True if the file was read and written successfully; False otherwise.
    """
    try:
        # Load existing records
        df = pd.read_json(filename, orient="records")
    except Exception:
        return False

    # Generate a new unique ID for this record
    new_id = str(uuid.uuid4())

    # Unpack bbox into four corners
    x1, y1, x2, y2 = bbox

    # Build the new record as a dict
    new_record = {
        "id": new_id,
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "trackerId": trackerId,
        "frameId": frameId,
        "class_id": class_id,
        "class_name": class_name,
        "confidence": confidence,
    }

    # Prepend the new record
    try:
        new_df = pd.concat([pd.DataFrame([new_record]), df], ignore_index=True)
    except Exception:
        return False

    # Write back to the same JSON file
    try:
        new_df.to_json(filename, orient="records", indent=2)
    except Exception:
        return False

    return True

annotation_agent = create_react_agent(   
    llm=llm,
    tools=[get_tool, update_tool, add_tool, delete_tool, undo_tool],
    prompt=prompt,)

chain = prompt | annotation_agent

def annotate_with_agent(question: str) -> str:
    return annotation_agent.invoke({"question": question,"intermediate_steps": []})

# while True:
#     print("\n\n-------------------------------")
#     question = input("Ask your question (q to quit): ")
#     print("\n\n")
#     if question == "q":
#         break
    
#     result = chain.invoke({"question": question})
#     print(result)