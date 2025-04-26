from flask import Flask, jsonify, send_from_directory, request
import os
from detector import process_video
from LLM.agents import annotate_with_agent
import pandas as pd
import json
import cv2

VIDEO_FOLDER = 'videos'
DATASETS_FOLDER = 'datasets'
os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(DATASETS_FOLDER, exist_ok=True)

app = Flask(__name__, 
            static_folder='static/react',  # React build files
            static_url_path='')

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Test endpoint!"})

@app.route('/api/videos', methods=['GET'])
def get_videos():
    videos = []
    for filename in os.listdir(VIDEO_FOLDER):
        if os.path.isfile(os.path.join(VIDEO_FOLDER, filename)) and any(filename.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.webm']):
            file_path = os.path.join(VIDEO_FOLDER, filename)
            file_size = os.path.getsize(file_path)
            videos.append({
                'name': filename,
                'size': file_size,
                'path': f'/api/videos/{filename}'  # URL path to access the video
            })
    
    return jsonify(videos)

@app.route('/api/videos/<filename>', methods=['GET'])
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

# What worked last time
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        file_name = file.filename.replace(' ', '_')
        file_path = os.path.join(VIDEO_FOLDER, file_name)
        file.save(file_path)
        print(f'File saved to {file_path}')
        return jsonify({'message': 'File uploaded successfully'}), 200
    
@app.route("/api/annotate", methods=['POST'])
@app.route("/api/annotate", methods=["POST"])
def annotate():
    # 1. Parse JSON body
    data = request.get_json(force=True)
    prompt = data.get("prompt", "")
    filename = data.get("filename")

    # 2. If they provided a filename, load its JSON and append to prompt
    combined_input = prompt
    if filename:
        try:
            df_file = pd.read_json(f"./datasets/{filename}.json", orient="records")
            # merge the annotations into the input prompt however you prefer
            combined_input += "\nExisting data:\n" + df_file.to_json(orient="records")
        except Exception as e:
            return jsonify({"error": f"Could not load '{filename}.json': {e}"}), 400

    # 3. Run the agent
    try:
        answer = annotate_with_agent(combined_input)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # 4. Turn the agent’s output into a DataFrame, then list-of-dicts
    try:
        df_answer = pd.DataFrame(answer)
        records = df_answer.to_dict(orient="records")
    except Exception:
        # if `answer` wasn’t list-of-dicts, just wrap it
        records = [answer]

    # 5. Return the records as JSON
    return jsonify(records)
    
@app.route('/api/process', methods=['POST'])
def process_video_endpoint():
    data = request.json
    if not data or 'video_name' not in data:
        return jsonify({'error': 'No video name provided'}), 400
    
    video_name = data['video_name'].replace(' ', '_')
    video_path = os.path.join(VIDEO_FOLDER, video_name)
    
    if not os.path.exists(video_path):
        return jsonify({'error': f'Video file {video_name} not found'}), 404
    
    try:
        # Process the video using the detector.py module
        process_video(video_name)
        
        # Get the JSON output file path
        json_name = video_name.split('.')[0] + '.json'
        json_path = os.path.join(DATASETS_FOLDER, json_name)
        
        if os.path.exists(json_path):
            return jsonify({
                'message': 'Video processed successfully',
                'video_name': video_name,
                'json_file': json_name
            }), 200
        else:
            return jsonify({'error': 'JSON file was not generated'}), 500
    except Exception as e:
        return jsonify({'error': f'Error processing video: {str(e)}'}), 500
    
@app.route('/api/detections/<filename>', methods=['GET'])
def get_detections(filename):
    # Remove file extension if present and add .json
    base_name = os.path.splitext(filename)[0]
    json_path = os.path.join(DATASETS_FOLDER, f"{base_name}.json")
    
    if not os.path.exists(json_path):
        return jsonify({'error': f'Detection file for {filename} not found'}), 404
    
    try:
        with open(json_path, 'r') as f:
            detections = json.load(f)
            
        # Get video metadata (fps, dimensions)
        video_path = os.path.join(VIDEO_FOLDER, filename)
        video_info = {}
        
        if os.path.exists(video_path):
            cap = cv2.VideoCapture(video_path)
            video_info = {
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
            }
            cap.release()
        
        return jsonify({
            'video_info': video_info,
            'detections': detections
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error reading detection file: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)