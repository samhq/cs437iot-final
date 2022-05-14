import json
import os
import datetime


def getDeviceFromId(deviceId):
    with open('devices.json') as json_file:
        data = json.load(json_file)

    device = {}

    for d in data:
        if d["id"] == deviceId:
            device = d
            break

    if "name" not in device:
        return {"found": False, "message": "Device not found"}

    return {"found": True, "data": device}


def getImages(data_path, devideId, base_path):
    files = []
    for file in os.listdir(data_path+"/"+devideId+"/images"):
        if file.endswith(".jpg") or file.endswith(".jpeg"):
            # files.append(os.path.join(path, file))
            s = file.split(".")[0].split("-")
            d = {
                "name": s[0],
                "date": datetime.datetime(int(s[2]), int(s[3]), int(s[4]), int(s[5]), int(s[6]), int(s[7])),
                "image": base_path+"/images/"+devideId + "/" + file
            }
        files.append(d)
    newlist = sorted(files, key=lambda d: d['date'], reverse=True) 
    return newlist
