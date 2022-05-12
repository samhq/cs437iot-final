import datetime
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray

with open('parameters.json', 'r') as jsonfile:
	params = json.load(jsonfile)

folder_path =  params[0]['images_path'] #"dataset/images"
name = 'Ayush'

cam = PiCamera()
cam.resolution = (512, 304)
cam.framerate = 10
rawCapture = PiRGBArray(cam, size=(512, 304))

img_counter = 0

while True:
    for frame in cam.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array
        cv2.imshow("Press Space to take a photo", image)
        rawCapture.truncate(0)

        k = cv2.waitKey(1)
        rawCapture.truncate(0)
        if k%256 == 27: # ESC pressed
            break
        elif k%256 == 32:
            # SPACE pressed
            #img_name = "dataset/"+ name +"/image_{}.jpg".format(img_counter)
            var_timestamp = str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")) 
            img_name = folder_path + "/" + name + "_" + str(img_counter) + "_" + var_timestamp + ".jpg"
            cv2.imwrite(img_name, image)
            print("{} written!".format(img_name))
            img_counter += 1

    if k%256 == 27:
        print("Escape hit, closing...")
        break

cv2.destroyAllWindows()
