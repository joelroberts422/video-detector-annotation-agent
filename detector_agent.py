"""
LangGraph Agent for analyzing YOLO detection JSON data
"""
import json
import os
from typing import Annotated, Dict, Literal, Sequence, TypedDict, Any, List
from typing_extensions import TypedDict

from dotenv import load_dotenv
import openai
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate

from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages

# Load environment variables
load_dotenv()

# Set up OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
# Initialize the OpenAI client carefully
def get_openai_client():
    try:
        return openai.OpenAI(api_key=api_key)
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return None

# Define agent state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    json_data: Dict[str, Any]
    class_info: Dict[str, str]

# Define model information about YOLO classes
YOLO_CLASS_INFO = {
    "0": "person",
    "1": "bicycle",
    "2": "car",
    "3": "motorcycle",
    "4": "airplane",
    "5": "bus",
    "6": "train",
    "7": "truck",
    "8": "boat",
    "9": "traffic light",
    "10": "fire hydrant",
    "11": "stop sign",
    "12": "parking meter",
    "13": "bench",
    "14": "bird",
    "15": "cat",
    "16": "dog",
    "17": "horse",
    "18": "sheep",
    "19": "cow",
    "20": "elephant",
    "21": "bear",
    "22": "zebra",
    "23": "giraffe",
    "24": "backpack",
    "25": "umbrella",
    "26": "handbag",
    "27": "tie",
    "28": "suitcase",
    "29": "frisbee",
    "30": "skis",
    "31": "snowboard",
    "32": "sports ball",
    "33": "kite",
    "34": "baseball bat",
    "35": "baseball glove",
    "36": "skateboard",
    "37": "surfboard",
    "38": "tennis racket",
    "39": "bottle",
    "40": "wine glass",
    "41": "cup",
    "42": "fork",
    "43": "knife",
    "44": "spoon",
    "45": "bowl",
    "46": "banana",
    "47": "apple",
    "48": "sandwich",
    "49": "orange",
    "50": "broccoli",
    "51": "carrot",
    "52": "hot dog",
    "53": "pizza",
    "54": "donut",
    "55": "cake",
    "56": "chair",
    "57": "couch",
    "58": "potted plant",
    "59": "bed",
    "60": "dining table",
    "61": "toilet",
    "62": "tv",
    "63": "laptop",
    "64": "mouse",
    "65": "remote",
    "66": "keyboard",
    "67": "cell phone",
    "68": "microwave",
    "69": "oven",
    "70": "toaster",
    "71": "sink",
    "72": "refrigerator",
    "73": "book",
    "74": "clock",
    "75": "vase",
    "76": "scissors",
    "77": "teddy bear",
    "78": "hair drier",
    "79": "toothbrush"
}

# Define graph nodes
def parse_json_data(state: AgentState) -> AgentState:
    """
    Process the JSON data to extract useful statistics
    """
    print("---PARSE JSON DATA---")
    json_data = state["json_data"]
    
    # Basic statistics
    total_frames = len(json_data)
    frame_sample = json_data[:min(3, total_frames)]
    
    # Count unique object classes and their occurrences
    class_counts = {}
    total_detections = 0
    
    for frame in json_data:
        if "detections" in frame:
            total_detections += len(frame["detections"])
            for detection in frame["detections"]:
                if "class_id" in detection:
                    class_id = str(detection["class_id"])
                    class_counts[class_id] = class_counts.get(class_id, 0) + 1
    
    # Convert class IDs to readable names
    class_info = state["class_info"]
    class_summary = []
    for class_id, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
        class_name = class_info.get(class_id, f"Unknown class {class_id}")
        class_summary.append(f"{class_name} ({count} instances)")
    
    # Create a message with the summary
    summary_message = f"""
JSON Analysis Summary:
- Total frames analyzed: {total_frames}
- Total object detections: {total_detections}
- Detected object classes: {len(class_counts)}

Most frequent objects:
{chr(10).join(f"- {item}" for item in class_summary[:5])}

Sample frame structure:
{json.dumps(frame_sample[0] if frame_sample else {}, indent=2)[:300]}...
"""
    
    # Add the message to the state
    message = HumanMessage(content=summary_message)
    return {"messages": [message], "json_data": json_data, "class_info": class_info}

def analyze_content(state: AgentState) -> AgentState:
    """
    Analyze the content of the video based on the detected objects
    """
    print("---ANALYZE CONTENT---")
    messages = state["messages"]
    json_data = state["json_data"]
    class_info = state["class_info"]
    
    # Prepare a prompt for the LLM to analyze the content
    prompt = PromptTemplate(
        template="""Analyze the following YOLO object detection data for a video:

{summary}

Focus your analysis on:
1. Object movement patterns over time/frames
2. Identify any anomalies or unexpected detections in the data
3. Spatial relationships between different detected objects
4. Temporal patterns (objects appearing/disappearing at certain points)
5. Potential errors or inconsistencies in the detection data

Provide specific observations about:
- Which objects are static vs. moving
- If any objects appear to be misclassified
- Frame-to-frame consistency of detections
- Any unusual or noteworthy patterns in confidence scores
- Objects that appear together frequently

Your analysis should be precise and focus on what the data actually reveals rather than assumptions.""",
        input_variables=["summary"],
    )
    
    # Get the summary from the first message
    summary = messages[0].content
    
    # Use the LLM to analyze
    try:
        model = ChatOpenAI(temperature=0.2, model="gpt-3.5-turbo", api_key=api_key)
        content_analysis = model.invoke(prompt.format(summary=summary))
        return {"messages": [content_analysis], "json_data": json_data, "class_info": class_info}
    except Exception as e:
        error_message = AIMessage(content=f"Error analyzing content: {str(e)}")
        return {"messages": [error_message], "json_data": json_data, "class_info": class_info}

def suggest_improvements(state: AgentState) -> AgentState:
    """
    Suggest improvements for the video object detection
    """
    print("---SUGGEST IMPROVEMENTS---")
    messages = state["messages"]
    json_data = state["json_data"]
    class_info = state["class_info"]
    
    prior_analysis = messages[-1].content
    
    prompt = PromptTemplate(
        template="""Based on the analysis of YOLO detection data:

{analysis}

Identify and address the following:

1. DATA QUALITY ISSUES:
   - Identify potential false positives or misclassifications
   - Note any temporal inconsistencies (objects flickering in/out between frames)
   - Highlight detection gaps where objects might be missed

2. TRACKING IMPROVEMENTS:
   - Suggest ways to improve tracking object movements across frames
   - Methods to handle occlusion or object overlap
   - Techniques to maintain object identity across frame transitions

3. DETECTION ENHANCEMENTS:
   - Recommendations for improving detection accuracy
   - Potential model adjustments or parameter tuning
   - Pre/post-processing techniques to address identified issues

4. ANALYSIS APPLICATIONS:
   - How this tracking data could be leveraged for specific use cases
   - Additional analytics that could extract more value from the data
   - Ways to visualize object movement patterns effectively

Be specific and provide actionable recommendations based directly on the detection data issues.""",
        input_variables=["analysis"],
    )
    
    try:
        model = ChatOpenAI(temperature=0.3, model="gpt-3.5-turbo", api_key=api_key)
        improvements = model.invoke(prompt.format(analysis=prior_analysis))
        return {"messages": [improvements], "json_data": json_data, "class_info": class_info}
    except Exception as e:
        error_message = AIMessage(content=f"Error suggesting improvements: {str(e)}")
        return {"messages": [error_message], "json_data": json_data, "class_info": class_info}

def compile_final_response(state: AgentState) -> AgentState:
    """
    Compile all analyses into a final response
    """
    print("---COMPILE FINAL RESPONSE---")
    messages = state["messages"]
    json_data = state["json_data"]
    class_info = state["class_info"]
    
    # Get the content from each stage
    summary = messages[0].content if len(messages) > 0 else "No summary available"
    analysis = messages[1].content if len(messages) > 1 else "No analysis available"
    improvements = messages[2].content if len(messages) > 2 else "No improvements available"
    
    final_prompt = PromptTemplate(
        template="""Create a comprehensive technical analysis of the YOLO detection data with these sections:

1. DETECTION SUMMARY:
{summary}

2. MOVEMENT ANALYSIS:
{analysis}

3. ERROR ASSESSMENT & RECOMMENDATIONS:
{improvements}

Your response MUST include:
- Precise analysis of object movements and trajectories
- Clear identification of detection errors and inconsistencies
- Temporal patterns across the video frames
- Evaluation of detection quality and reliability
- Concrete actionable recommendations for improving detection

Focus on providing a data-driven, technical assessment that would be valuable for improving both the detection model and post-processing pipeline. Be specific about errors found and prioritize the most important findings.""",
        input_variables=["summary", "analysis", "improvements"],
    )
    
    try:
        model = ChatOpenAI(temperature=0.1, model="gpt-3.5-turbo", api_key=api_key)
        final_response = model.invoke(final_prompt.format(
            summary=summary,
            analysis=analysis,
            improvements=improvements
        ))
        return {"messages": [final_response], "json_data": json_data, "class_info": class_info}
    except Exception as e:
        error_message = AIMessage(content=f"Error compiling final response: {str(e)}")
        return {"messages": [error_message], "json_data": json_data, "class_info": class_info}

# Build the graph
def build_agent_graph():
    """
    Build and return the LangGraph for YOLO JSON analysis
    """
    # Define the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("parse_json", parse_json_data)
    workflow.add_node("analyze_content", analyze_content)
    workflow.add_node("suggest_improvements", suggest_improvements)
    workflow.add_node("compile_final", compile_final_response)
    
    # Add edges - linear flow for this case
    workflow.add_edge(START, "parse_json")
    workflow.add_edge("parse_json", "analyze_content")
    workflow.add_edge("analyze_content", "suggest_improvements")
    workflow.add_edge("suggest_improvements", "compile_final")
    workflow.add_edge("compile_final", END)
    
    # Compile the graph
    return workflow.compile()

# Function to run the agent with a JSON file
def analyze_json_with_agent(json_file_path):
    """
    Analyze a JSON file using the LangGraph agent
    
    Args:
        json_file_path: Path to the JSON file
        
    Returns:
        The final message from the agent
    """
    try:
        # Load JSON data
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)
        
        # Build the graph
        graph = build_agent_graph()
        
        # Prepare the initial state
        initial_state = {
            "messages": [],
            "json_data": json_data,
            "class_info": YOLO_CLASS_INFO
        }
        
        # Execute the graph
        result = graph.invoke(initial_state)
        
        # Return the final message
        if result["messages"] and len(result["messages"]) > 0:
            return result["messages"][-1].content
        else:
            return "No analysis could be generated."
            
    except Exception as e:
        return f"Error analyzing JSON with agent: {str(e)}"

if __name__ == "__main__":
    # Test the agent
    test_file = "datasets/test.json"
    if os.path.exists(test_file):
        print(analyze_json_with_agent(test_file))
    else:
        print(f"Test file {test_file} not found.") 