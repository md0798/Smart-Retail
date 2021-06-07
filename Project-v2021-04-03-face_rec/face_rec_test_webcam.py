'''
Name: Aditya Wikara
UNI: aw3306
Name: Meet Desai
UNI: mpd2155
Name: Rifqi Luthfan
UNI: rl3154

Date: 2021-04-01
'''

import face_recognition
import cv2
import numpy as np
import pandas as pd
import uuid
import requests
import json
import datetime as dt
from bson import json_util
import time

# from collections import Counter
# counter = Counter(y)
# most_common = counter.most_common(1)[0][0]
# return(most_common)

# This is a demo of running face recognition on live video from your webcam. It's a little more complicated than the
# other example, but it includes some basic performance tweaks to make things run a lot faster:
#   1. Process each video frame at 1/4 resolution (though still display it at full resolution)
#   2. Only detect faces in every other frame of video.

# PLEASE NOTE: This example requires OpenCV (the `cv2` library) to be installed only to read from your webcam.
# OpenCV is *not* required to use the face_recognition library. It's only required if you want to run this
# specific demo. If you have trouble installing it, try any of the other demos that don't require it instead.


headers = {"Content-Type": "application/json"}
#url = "http://localhost:5000"
url = "http://18.224.8.222:5000"

temp = requests.get(url+"/get_face")
#df_face_encoding = pd.DataFrame(temp.json()["current_document"])
df_face_encoding = pd.DataFrame(temp.json())

df_face_encoding["face_encoding"] = df_face_encoding["face_encoding"].apply(lambda x: np.array(x))

known_face_encodings = list(df_face_encoding["face_encoding"])
known_face_names = list(df_face_encoding["customer_id"])


"""
# Load a sample picture and learn how to recognize it.
fiqi_image = face_recognition.load_image_file("./Fiqi.jpg")
fiqi_face_encoding = face_recognition.face_encodings(fiqi_image)[0]

# Load a sample picture and learn how to recognize it.
obama_image = face_recognition.load_image_file("obama.jpg")
obama_face_encoding = face_recognition.face_encodings(obama_image)[0]

# Load a second sample picture and learn how to recognize it.
biden_image = face_recognition.load_image_file("biden.jpg")
biden_face_encoding = face_recognition.face_encodings(biden_image)[0]

# Create arrays of known face encodings and their names
known_face_encodings = [
    obama_face_encoding,
    biden_face_encoding,
    fiqi_face_encoding
]
known_face_names = [
    "Barack Obama",
    "Joe Biden",
    "Fiqi"
]
"""

# Get a reference to webcam #0 (the default one)
video_capture = cv2.VideoCapture(0)
# video_capture = cv2.VideoCapture("http://160.39.197.197:8000/stream.mjpg")

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

# Frame buffer
buffer_frame = [""]*100
## Send data only when first detect new unique customer
curr_customer = None

## Initialize JSON for time in time out
detect_time = {'method':'', 'customer_id': '', 'time_in': '', 'time_out': ''}

while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Only process every other frame of video to save time
    if process_this_frame:
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # # If a match was found in known_face_encodings, just use the first one.
            # if True in matches:
            #   first_match_index = matches.index(True)
            #   name = known_face_names[first_match_index]

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            if name == "Unknown":
                name = str(uuid.uuid4())
                temp = {'customer_id': name, 'face_encoding': list(face_encoding)}
                res = requests.post(url+"/submit_face/", headers=headers, data=json.dumps(temp))
                known_face_names.append(name)
                known_face_encodings.append(face_encoding)            

            face_names.append(name)
        
        if not face_names:
            buffer_frame.append("")
        else:
            buffer_frame.append(face_names[0])
        buffer_frame.pop(0)
        
        if buffer_frame[-1]:
            # not null last value of buffer
            if curr_customer != buffer_frame[-1]:
                # new customer
                if (curr_customer is not None):
                    # if there is existing customer in buffer, set timeout
                    time_out = dt.datetime.utcnow()#.strftime("%Y-%m-%d %H:%M:%S")
                    detect_time["method"] = "update"
                    detect_time["customer_id"] = curr_customer
                    detect_time["time_out"] = time_out
                    res = requests.post(url+"/detect_face/", headers=headers, data=json.dumps(detect_time, default=json_util.default))
                    print(res.json())
                # set time in new customer
                time_in = dt.datetime.utcnow()#.strftime("%Y-%m-%d %H:%M:%S")
                curr_customer = buffer_frame[-1]
                detect_time["method"] = "insert"
                detect_time["customer_id"] = curr_customer
                detect_time["time_in"] = time_in
                detect_time["time_out"] = ''
                print(detect_time)
                res = requests.post(url+"/detect_face/", headers=headers, data=json.dumps(detect_time, default=json_util.default))
                print(res.json())
                # time.sleep(15)
        else:
            # null last value
            if (not buffer_frame[0]) and (curr_customer is not None):
                # if already no face detected for buffer size, set timeout
                time_out = dt.datetime.utcnow()#.strftime("%Y-%m-%d %H:%M:%S")
                detect_time["method"] = "update"
                detect_time["customer_id"] = curr_customer
                detect_time["time_out"] = time_out
                print(detect_time)
                res = requests.post(url+"/detect_face/", headers=headers, data=json.dumps(detect_time, default=json_util.default))
                curr_customer = None
                print(res.json())

    process_this_frame = not process_this_frame


    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()