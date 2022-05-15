# import the necessary packages
import face_recognition
import imutils
import pickle
import time
import cv2
import requests
import os
import json
import datetime
import requests
from dotenv import dotenv_values
import picamera

config = dotenv_values(".env")

dir_path = os.path.dirname(os.path.realpath(__file__))
data_path = dir_path+"/data"
settings_path = data_path+"/settings.json"
encodings_path = data_path+"/encodings.pickle"
images_path = data_path+"/images"
server_url = config["SERVER_URL"]

def upload_images(images):
    params = load_params()
    if params["found"]:
        d = {}
        for i in images:
            image_file = open(i, "rb")
            r = requests.post(server_url+"/upload/"+params["data"]["deviceId"],
                              files={"image_file": image_file})
            if not r.ok:
                d[i] = "ERROR"
            else:
                d[i] = "SUCCESS"

        return d
    else:
        return "Settings file not found"


def send_email(img, name=""):
    params = load_params()
    to_emails = config["DEFAULT_TO_EMAILS"].split(",")
    if params["found"] and len(params["found"]["notificationEmails"]) > 0:
        to_emails = params["found"]["notificationEmails"]

    subject = "Somebody came at your house"
    message = "Somebody is at your door"
    if name != "":
        subject = name + " came to visit you"
        message = name + " is at your door"

    r = requests.post(
        config["MAILGUN_URL"],
        auth=("api", config["MAILGUN_API_KEY"]),
        files=[("attachment", (img, open(img, "rb").read()))],
        data={"from": config["SENDER_EMAIL"],
              "to": to_emails,
              "subject": subject,
              "html": "<html><body>" + message + "</body></html>"})

    if not r.ok:
        return "ERROR"

    return "SUCCESS"


def load_params():
    try:
        with open(settings_path, 'r') as jsonfile:
            params = json.load(jsonfile)
    except:
        return {"found": False, "params": ""}

    return {"found": False, "params": params}


def load_encodings():
    if os.path.exists(encodings_path):
        try:
            data = pickle.loads(open(encodings_path, "rb").read())
        except:
            return {"found": False, "data": ""}
        return {"found": True, "data": data}
    return {"found": False, "data": ""}


def detect_from_image(camera):
    # Initialize 'currentname' to trigger only when a new person is identified.
    currentname = "unknown"
    name = ""

    # use this xml file
    cascade = "haarcascade_frontalface_default.xml"
    print("[INFO]: face detector...")
    detector = cv2.CascadeClassifier(cascade)
    
    camera.capture("img.jpg")
    print("Image Captured")

    frame = cv2.imread("img.jpg")
    print("Read frame")
    
    # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = imutils.resize(frame, width=500)
    print("Frame resize")
    
    # convert the input frame from (1) BGR to grayscale (for face
    # detection) and (2) from BGR to RGB (for face recognition)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # detect faces in the grayscale frame
    rects = detector.detectMultiScale(gray, scaleFactor=1.1,
                                    minNeighbors=5, minSize=(30, 30),
                                    flags=cv2.CASCADE_SCALE_IMAGE)
    
    # OpenCV returns bounding box coordinates in (x, y, w, h) order
    # but we need them in (top, right, bottom, left) order, so we
    # need to do a bit of reordering
    boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]
    print("Boxes")
    
    encs = load_encodings()
    img_name = ""
    print("Encs", encs)
    if encs["found"]:
        # compute the facial embeddings for each face bounding box
        encodings = face_recognition.face_encodings(rgb, boxes)
        names = []
        name = "Unknown"
        # loop over the facial embeddings
        for encoding in encodings:
            # attempt to match each face in the input image to our known
            # encodings
            matches = face_recognition.compare_faces(
                encs["data"]["encodings"], encoding)
            # check to see if we have found a match
            if True in matches:
                # find the indexes of all matched faces then initialize a
                # dictionary to count the total number of times each face
                # was matched
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}
                # loop over the matched indexes and maintain a count for
                # each recognized face face
                for i in matchedIdxs:
                    name = encs["data"]["names"][i]
                    counts[name] = counts.get(name, 0) + 1
                # determine the recognized face with the largest number
                # of votes (note: in the event of an unlikely tie Python
                # will select first entry in the dictionary)
                name = max(counts, key=counts.get)
                # If someone in your dataset is identified, print their name on the screen
                if currentname != name:
                    #currentname = name
                    print(name)
                    if name != "Unknown":  # Recognized Person
                        img_cnt = len([entry for entry in os.listdir(
                            images_path) if os.path.isfile(os.path.join(images_path, entry))]) + 1
                        var_timestamp = str(
                            datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
                        img_name = images_path+"/"+name+"-" + \
                            str(img_cnt)+"-" + var_timestamp+".jpg"
                        cv2.imwrite(img_name, frame)
                        print(
                            '[INFO]: Taking a picture and Saving it for more training purposes')
                        os.system(
                            'espeak -ven+f1 -g5 -s160 "Welcome ' + str(name) + '"')
            # update the list of names
            names.append(name)

    # ===== If Image is not present in DB =====
    #print(f"name, currentname:{name},{currentname}")
    if currentname != name and name == 'Unknown':
        print(f"Visitor: {name}")
        # Take a picture to send in the email
        img_cnt = len([entry for entry in os.listdir(images_path)
                    if os.path.isfile(os.path.join(images_path, entry))]) + 1
        var_timestamp = str(
            datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
        img_name = images_path + "/Unknown-" + \
            str(img_cnt) + "-" + var_timestamp + ".jpg"
        cv2.imwrite(img_name, frame)
        print('[INFO]: Taking a picture and Saving it in Visitors Log.')
        os.system(
            'espeak -ven+f1 -g5 -s160 "Welcome! Someone will be with you shortly."')
    # ======================================================
    em = send_email(img_name, name)
    print("[INFO]: Sending email: ", em)
    up = upload_images([img_name])
    print("[INFO]: Uploading images: ", up)

    os.remove("img.jpg")
    os.remove(img_name)
    
    print("[INFO]: Removed image")
            
    currentname = name
    cv2.destroyAllWindows()
