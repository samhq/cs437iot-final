from imutils import paths
import face_recognition
import pickle
import cv2
import os


def trainModelFromImages(imageDir, encodingPath):
    try:
        # our images are located in the dataset folder
        print("[INFO] start processing faces...")
        # imageDir = "dataset/images"
        imagePaths = list(sorted(paths.list_images(imageDir)))
        # print(imagePaths)
        # initialize the list of known encodings and known names
        knownEncodings = []
        knownNames = []
        foundImgNames = []

        # Find Different Names in Image Paths
        for (i, imagePath) in enumerate(imagePaths):
            val = imagePath.split(os.path.sep)[-1].split("-")[0]
            foundImgNames.append(val)
        # Remove duplicate names from images
        foundImgNames = set(foundImgNames)

        for name in foundImgNames:
            SelimagePaths = []
            for i in os.listdir(imageDir):
                if i.find(name) != -1:
                    SelimagePaths.append(imageDir+"/"+i)
            # loop over the image paths
            # print(f"SelimagePaths:{SelimagePaths}")
            for (i, imagePath) in enumerate(SelimagePaths):
                # extract the person name from the image path
                print("[INFO] processing image for {} {}/{}".format(name,
                      i + 1, len(SelimagePaths)))
                # load the input image and convert it from RGB (OpenCV ordering)
                # to dlib ordering (RGB)
                image = cv2.imread(imagePath)
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # detect the (x, y)-coordinates of the bounding boxes
                # corresponding to each face in the input image
                boxes = face_recognition.face_locations(rgb, model="hog")

                # compute the facial embedding for the face
                encodings = face_recognition.face_encodings(rgb, boxes)

                # loop over the encodings
                for encoding in encodings:
                    # add each encoding + name to our set of known names and
                    # encodings
                    knownEncodings.append(encoding)
                    knownNames.append(name)

        # dump the facial encodings + names to disk
        print("[INFO] serializing encodings...")
        data = {"encodings": knownEncodings, "names": knownNames}
        f = open(encodingPath, "wb")
        f.write(pickle.dumps(data))
        f.close()
    except:
        return False
    
    return True
