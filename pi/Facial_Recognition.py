#! /usr/bin/python

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import imutils
import pickle
import time
import cv2
import requests
from gpiozero import MotionSensor
import os
from espeak import espeak
import json
import datetime

with open('parameters.json', 'r') as jsonfile:
	params = json.load(jsonfile)

img_path =  params[0]['images_path'] #"dataset/images"

#Initialize 'currentname' to trigger only when a new person is identified.
currentname = "unknown"
name = ""
#Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "encodings.pickle"
#use this xml file
cascade = "haarcascade_frontalface_default.xml"

pir = MotionSensor(4)

#function for setting up emails
def send_message(name,img, from_email,to_email):
    return requests.post(
        "https://api.mailgun.net/v3/sandbox74667d33f04c457798cafe211b51ce0f.mailgun.org/messages",
        auth=("api", "facd17ed1483ee93b6995c05ae25e37b-fe066263-e603fb88"),
        files = [("attachment", (img, open(img, "rb").read()))],
        data={"from": from_email,
            "to": [to_email],
            "subject": "You have a visitor",
            "html": "<html>" + name + " is at your door.  </html>"})

# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO]: Loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())
detector = cv2.CascadeClassifier(cascade)

# initialize the video stream and allow the camera sensor to warm up
# print("[INFO] starting video stream...")
vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

# start the FPS counter
fps = FPS().start()
motion=0
while True:
	pir.wait_for_motion()
	if motion == 0:
		print("[ALERT]: Motion Detected, Starting the Video Feed")
		print("[INFO]: Starting video stream...")
	motion=1
	#fps = FPS().start()
	# grab the frame from the threaded video stream and resize it
	# to 500px (to speedup processing)
	frame = vs.read()
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

	# compute the facial embeddings for each face bounding box
	encodings = face_recognition.face_encodings(rgb, boxes)
	names = []
	name = "Unknown"
	# loop over the facial embeddings
	for encoding in encodings:
		# attempt to match each face in the input image to our known
		# encodings
		matches = face_recognition.compare_faces(data["encodings"],encoding)
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
				name = data["names"][i]
				counts[name] = counts.get(name, 0) + 1
			# determine the recognized face with the largest number
			# of votes (note: in the event of an unlikely tie Python
			# will select first entry in the dictionary)
			name = max(counts, key=counts.get)
			#If someone in your dataset is identified, print their name on the screen
			if currentname != name:
				#currentname = name
				print(f"{params[0]['greeting']},{name}")
				if name != "Unknown": # Recognized Person
					#img_cnt = len([entry for entry in os.listdir(img_path) if os.path.isfile(os.path.join(img_path, entry))]) + 1
					#var_timestamp = str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")) 
					#img_name = img_path+"/"+name+"_"+str(img_cnt)+"_" + var_timestamp+".jpg"
					#cv2.imwrite(img_name, frame)
					#print('[INFO]: Taking a picture and Saving it for more training purposes')
					os.system('espeak -ven+f1 -g5 -s160 "' + params[0]['greeting'] + str(name) + '"')
		# update the list of names
		names.append(name)
	# loop over the recognized faces
	for ((top, right, bottom, left), name) in zip(boxes, names):
		# draw the predicted face name on the image - color is in BGR
		cv2.rectangle(frame, (left, top), (right, bottom),
			(0, 255, 225), 2)
		y = top - 15 if top - 15 > 15 else top + 15
		cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
			.8, (0, 255, 255), 2)

    # ===== If Image is not present in DB =====
	#print(f"name, currentname:{name},{currentname}")
	if currentname != name and name == 'Unknown':
		print(f"Visitor: {name}")
		#Take a picture to send in the email
		img_cnt = len([entry for entry in os.listdir(img_path) if os.path.isfile(os.path.join(img_path, entry))]) + 1
		var_timestamp = str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")) 
		img_name = img_path + "/" + "Unknown_" + str(img_cnt) + "_" + var_timestamp +".jpg"
		cv2.imwrite(img_name, frame)
		os.system('espeak -ven+f1 -g5 -s160 "' + params[1]['greeting'] + '"')
		print('[INFO]: Taking a picture and Saving it in Visitors Log.')
		#Now send me an email to let me know who is at the door
		request = send_message(name,img_name,params[1]['from_email'],params[1]['to_email'])
		print ('Email Status Code: '+format(request.status_code)) #200 status code means email sent successfully
		if request.status_code == 200:
			print('[INFO]: Email Notification Sent to the Owner')
		else:
			print('[ERR]: Error Sending Email Notification to the Owner')
    # ======================================================
	currentname = name
    # display the image to our screen
	cv2.imshow("Facial Recognition is Running", frame)
	key = cv2.waitKey(1) # & 0xFF
	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break
	# update the FPS counter
	fps.update()
	#pir.wait_for_no_motion()
	motion=0

# stop the timer and display FPS information
fps.stop()
print("[INFO]: Elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO]: Approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
