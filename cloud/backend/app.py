from flask import Flask, request, send_file
from flask_cors import CORS
import json
from train_model import trainModelFromImages
from utils import getDeviceFromId, getImages
import os
import shutil
import requests
from werkzeug.utils import secure_filename
from dotenv import dotenv_values

config = dotenv_values(".env")
dir_path = os.path.dirname(os.path.realpath(__file__))
data_path = dir_path+"/data"
base_path = config["BASE_URL"]

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    if not os.path.exists('devices.json'):
        shutil.copyfile(dir_path+"/sample_devices.json",
                        dir_path+"/devices.json")

    return {"message": "SGSS Backend Service"}, 200


@app.route("/devices", methods=['GET', 'POST'])
def getDevices():
    with open('devices.json') as json_file:
        data = json.load(json_file)

    if request.method == 'POST':
        # print(request.json)
        d = {
            "id": request.json['id'],
            "name": request.json['name'],
            "live_url": request.json['liveFeed'],
            "api_url": request.json['apiUrl'],
        }
        data.append(d)
        directories = [data_path+"/"+d["id"], data_path+"/"+d["id"]+"/images"]
        for dirs in directories:
            if not os.path.exists(dirs):
                os.makedirs(dirs)

        shutil.copyfile(dir_path+"/sample_settings.json",
                        data_path+"/"+d["id"]+"/settings.json")

        with open('devices.json', 'w') as outfile:
            json.dump(data, outfile, indent=4)
        return {"error": False, "message": "Successfully added"}, 200
    else:
        return {"error": False, "data": data}, 200


@app.route("/devices/delete", methods=['POST'])
def deleteDevices():
    with open('devices.json') as json_file:
        data = json.load(json_file)

    print(request.json)
    delId = request.json['id']

    device = getDeviceFromId(delId)

    if not device["found"]:
        return {"message": "Device not found"}, 404

    for d in data:
        if d["id"] == delId:
            data.remove(d)
            break

    with open('devices.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)

    return {"error": False, "message": "Successfully deleted"}, 200


@app.route("/history/<deviceId>", methods=["GET"])
def getHistory(deviceId):
    device = getDeviceFromId(deviceId)

    if not device["found"]:
        return {"message": "Device not found"}, 404

    imgs = getImages(data_path, deviceId, base_path)
    return {"error": False, "data": imgs}, 200


@app.route("/settings/<deviceId>", methods=["GET"])
def getSettings(deviceId):
    device = getDeviceFromId(deviceId)

    if not device["found"]:
        return {"message": "Device not found"}, 404

    settings_path = data_path+"/"+deviceId+"/settings.json"

    with open(settings_path) as json_file:
        data = json.load(json_file)
    return {"error": False, "data": json.dumps(data)}, 200


@app.route("/settings/<deviceId>", methods=["POST"])
def postSettings(deviceId):
    device = getDeviceFromId(deviceId)

    if not device["found"]:
        return {"message": "Device not found"}, 404

    settings_path = data_path+"/"+deviceId+"/settings.json"
    # print(request.json)
    data = json.loads(request.json['settings'])

    with open(settings_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    # SEND DATA TO PI SERVER
    headers = {'content-type': 'application/json'}
    r = requests.post(device["data"]["api_url"]+"/upload/settings",
                      headers=headers, data=json.dumps({"settings": json.dumps(data)}))
    if not r.ok:
        return {"error": True, "message": "Sending data to device failed"}, 404

    return {"error": False, "data": data}, 200


@app.route("/train/<deviceId>")
def trainImage(deviceId):
    device = getDeviceFromId(deviceId)

    if not device["found"]:
        return {"message": "Device not found"}, 404

    encode_path = data_path+"/"+deviceId+"/encodings.pickle"
    images_path = data_path+"/"+deviceId+"/images"

    train = trainModelFromImages(images_path, encode_path)
    # train = False
    if not train:
        return {"error": True, "message": "Cannot train now"}, 503

    # SEND FILE TO PI SERVER
    enc_file = open(encode_path, "rb")
    # headers = {'content-type': 'application/json'}
    r = requests.post(device["data"]["api_url"]+"/upload/encodings",
                      files={"encodings_file": enc_file})
    if not r.ok:
        return {"error": True, "message": "Sending file to device failed"}, 404

    return {"error": False, "message": "File sent successfully"}, 200


@app.route("/images/<deviceId>/<filename>", methods=["GET"])
def getImage(deviceId, filename):
    device = getDeviceFromId(deviceId)

    if not device["found"]:
        return {"message": "Device not found"}, 404

    image_path = data_path+"/"+deviceId+"/images/"+filename
    if not os.path.exists(image_path):
        return {"message": "Image not found"}, 404

    return send_file(image_path, mimetype='image/jpg')
    # return {"error": False, "data": json.dumps(data)}, 200


@app.route("/images/rename/<deviceId>/<filename>", methods=["POST"])
def Image(deviceId, filename):
    device = getDeviceFromId(deviceId)

    if not device["found"]:
        return {"message": "Device not found"}, 404

    image_path = data_path+"/"+deviceId+"/images/"+filename
    if not os.path.exists(image_path):
        return {"message": "Image not found"}, 404

    newName = request.json["updated_name"]
    s = filename.split("-")
    s[0] = newName.strip()
    newFilename = '-'.join(s)
    updated_path = data_path+"/"+deviceId+"/images/"+newFilename

    os.rename(image_path, updated_path)

    return {"error": False, "message": "Successfully updated"}, 200


@app.route('/upload/<deviceId>', methods=['POST'])
def upload_file(deviceId):
    file = request.files['image_file']
    path_to_save = data_path + "/"+deviceId + \
        "/images/"+secure_filename(file.filename)
    file.save(path_to_save)

    return {"error": False, "message": "Successfully uploaded"}, 200
