from flask import Flask, request
from flask_cors import CORS
import json
import os


dir_path = os.path.dirname(os.path.realpath(__file__))
data_path = dir_path+"/data"
settings_path = data_path+"/settings.json"
encodings_path = data_path+"/encodings.pickle"
images_path = data_path+"/images"

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return {"message": "SGSS Pi Service"}, 200

@app.route('/upload/settings', methods=['POST'])
def settings():
    data = json.loads(request.json['settings'])

    with open(settings_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    return {"error": False, "message": "Successfully updated"}, 200

@app.route('/upload/encodings', methods=['POST'])
def encodings():
    file = request.files['encodings_file']
    file.save(encodings_path)

    return {"error": False, "message": "Successfully uploaded"}, 200

def start_api_server():
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)
