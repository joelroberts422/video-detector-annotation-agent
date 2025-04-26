<<<<<<< HEAD
from flask import Flask, jsonify, send_from_directory


app = Flask(__name__, 
            static_folder='static/react',  # React build files
            static_url_path='/app')
=======
from flask import Flask, jsonify, send_from_directory, request
import os


VIDEO_FOLDER = 'videos'
DATASETS_FOLDER = 'datasets'
os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(DATASETS_FOLDER, exist_ok=True)

app = Flask(__name__, 
            static_folder='static/react',  # React build files
            static_url_path='')
>>>>>>> b5bf8e679c938e015dcb00daa6217e98f28b3a74

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Test endpoint!"})

<<<<<<< HEAD
=======
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

>>>>>>> b5bf8e679c938e015dcb00daa6217e98f28b3a74

if __name__ == '__main__':
    app.run(debug=True)