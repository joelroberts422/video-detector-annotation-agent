from flask import Flask, jsonify, send_from_directory, request
import os
from detector import process_video
import json
import openai
from dotenv import load_dotenv
from detector_agent import analyze_json_with_agent

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
# Initialize OpenAI client
client = openai.OpenAI(api_key=openai_api_key)

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

@app.route('/api/processed', methods=['GET'])
def get_processed_videos():
    """Return a list of all processed JSON files in the datasets folder"""
    processed_files = []
    for filename in os.listdir(DATASETS_FOLDER):
        if os.path.isfile(os.path.join(DATASETS_FOLDER, filename)) and filename.endswith('.json'):
            processed_files.append(filename)
    
    return jsonify(processed_files)

@app.route('/api/datasets/<filename>', methods=['GET'])
def serve_dataset(filename):
    """Serve a dataset JSON file"""
    return send_from_directory(DATASETS_FOLDER, filename)

@app.route('/api/analyze', methods=['POST'])
def analyze_json():
    """Analyze a JSON file using the LangGraph agent"""
    data = request.json
    if not data or 'json_file' not in data:
        return jsonify({'error': 'No JSON file provided'}), 400
    
    json_file = data['json_file']
    json_path = os.path.join(DATASETS_FOLDER, json_file)
    
    if not os.path.exists(json_path):
        return jsonify({'error': f'JSON file {json_file} not found'}), 404
    
    try:
        # Use the LangGraph agent to analyze the JSON file
        analysis = analyze_json_with_agent(json_path)
        
        return jsonify({
            'analysis': analysis
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error analyzing JSON: {str(e)}'}), 500

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

if __name__ == '__main__':
    app.run(debug=True)