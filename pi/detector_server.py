# import the necessary packages
import face_recognition
import imutils
import pickle
import time
import cv2
import requests
from gpiozero import MotionSensor
import os, signal, threading
import json
import datetime
import picamera
import requests
from dotenv import dotenv_values
import subprocess
from subprocess import check_call, call
import sys
import glob
import time

config = dotenv_values(".env")

tmp_image = "image.jpg"
dir_path = os.path.dirname(os.path.realpath(__file__))
data_path = dir_path+"/data"
settings_path = data_path+"/settings.json"
encodings_path = data_path+"/encodings.pickle"
images_path = data_path+"/images"
server_url = config["SERVER_URL"]
pir = MotionSensor(4)

ipath = dir_path+"/video_streaming_server.py"    #CHANGE THIS PATH TO THE LOCATION OF live.py

def thread_second():
    call(["python3", ipath])

def check_kill_process(pstring):
    print(f"Inside Check Kill:{pstring}")
    for line in os.popen("ps ax | grep " + pstring + " | grep -v grep"):
        print(f"line:{line}")
        fields = line.split()
        print(fields)
        pid = fields[0]
        print(pid)
        os.kill(int(pid), signal.SIGKILL)

# ==========================


def upload_images(images):
    params = load_params()
    if params["found"]:
        ok = 0
        notok = 0
        for i in images:
            image_file = open(i, "rb")
            r = requests.post(server_url+"/upload/"+params["params"]["deviceId"],
                              files={"image_file": image_file})
            if not r.ok:
                notok = notok + 1
            else:
                ok = ok + 1

        return "Ok: "+str(ok)+", Not Ok: "+str(notok)
    else:
        return "Settings file not found"


def send_email(img, name=""):
    params = load_params()
    to_emails = config["DEFAULT_TO_EMAILS"].split(",")
    if params["found"] and len(params["params"]["notificationEmails"]) > 0:
        to_emails = params["params"]["notificationEmails"]

    # print(to_emails)
    
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
    # print(settings_path)
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as jsonfile:
            params = json.load(jsonfile)
        return {"found": True, "params": params}
    return {"found": False, "params": ""}


def load_encodings():
    # print(encodings_path)
    if os.path.exists(encodings_path):
        data = pickle.loads(open(encodings_path, "rb").read())

        return {"found": True, "data": data}
    return {"found": False, "data": ""}


def start_detector_server():
    # use this xml file
    cascade = "haarcascade_frontalface_default.xml"
    print("[INFO]: face detector...")
    detector = cv2.CascadeClassifier(cascade)

    # initialize the video stream and allow the camera sensor to warm up
    # print("[INFO] starting video stream...")
    #---AK vs = VideoStream(usePiCamera=True).start()
    #time.sleep(2.0)

    # start the FPS counter
    #fps = FPS().start()
    lastTime = 0
    currentTime = time.time()
    while currentTime - lastTime > 30:
        # Initialize 'currentname' to trigger only when a new person is identified.
        currentname = ""
        name = "Unknown"
        
        try:
            pir.wait_for_motion()
            print("Motion detected")
            # grab the frame from the threaded video stream and resize it
            # to 500px (to speedup processing)
            #------
            check_kill_process('video_streaming_server.py')
            time.sleep(2)            
            print("Stream ended.")
            # take picture with camera
            with picamera.PiCamera() as camera:
                #change resolution to get better latency
                print("Capturing picture...")
                camera.resolution = (640,480)
                print("Resolution set")
                camera.capture(tmp_image)     #CHANGE PATH TO YOUR USB THUMBDRIVE
                print("Captured picture")
                time.sleep(2)
                camera.close()
                print("Closing camera")
                
            # alert picture taken
            print("Picture taken.")

            #frame = vs.read()
            frame = cv2.imread(tmp_image) 
            frame = imutils.resize(frame, width=500)
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
            print("boxes detected", str(len(boxes)))

            if len(boxes) > 0:
                encs = load_encodings()
                img_name = ""
                # print("encs", encs)

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
                print("name, currentname:", name, currentname)

                if currentname != name and name == 'Unknown':
                    print(f"Visitor: {name}")
                    # Take a picture to send in the email
                    img_cnt = len([entry for entry in os.listdir(images_path)
                                if os.path.isfile(os.path.join(images_path, entry))]) + 1
                    print("cnt", img_cnt)
                    var_timestamp = str(
                        datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
                    print("tm", var_timestamp)
                    img_name = images_path + "/Unknown-" + \
                        str(img_cnt) + "-" + var_timestamp + ".jpg"
                    print("img", img_name)
                    cv2.imwrite(img_name, frame)

                    print('[INFO]: Taking a picture and Saving it in Visitors Log.')
                    os.system(
                        'espeak -ven+f1 -g5 -s160 "Welcome! Someone will be with you shortly."')

                up = upload_images([img_name])
                print("[INFO]: Uploading images: ", up)
                em = send_email(img_name, name)
                print("[INFO]: Sending email: ", em)
                os.remove(img_name)
                os.remove(tmp_image)
                print("[INFO]: Removed image")
                currentname = name
            
                lastTime = currentTime
            
            # update the FPS counter
            #fps.update()
            #----------------
            # run live stream again
            processThread = threading.Thread(target=thread_second)
            processThread.start()
            print("Stream running. Refresh page.")

            pir.wait_for_no_motion()
            time.sleep(2)
        except Exception as e:
            print("[ERROR]: Exception: ", e)
            break

    # stop the timer and display FPS information
    #fps.stop()
    #print("[INFO]: Elasped time: {:.2f}".format(fps.elapsed()))
    #print("[INFO]: Approx. FPS: {:.2f}".format(fps.fps()))

    # do a bit of cleanup
    cv2.destroyAllWindows()
    # vs.stop()

if __name__ == "__main__":
    start_detector_server()
