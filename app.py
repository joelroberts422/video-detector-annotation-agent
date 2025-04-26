from flask import Flask, jsonify, send_from_directory


app = Flask(__name__, 
            static_folder='static/react',  # React build files
            static_url_path='')

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Test endpoint!"})


if __name__ == '__main__':
    app.run(debug=True)