import face_recognition
import cv2
from onvif import ONVIFCamera
import zeep
import math
from time import sleep
from imutils.video import VideoStream
import imutils

n = int(input("press 1 for webcam and 2 for 192.168.15.43 \n"))

if n == 1:
    video_capture = cv2.VideoCapture(-1)
elif n == 2:
    video_capture = VideoStream(src="rtsp://192.168.15.43:554/Streaming/Channels/1").start()
else:
    print("wrong input")

face_locations = []
i = 0

cam = ONVIFCamera('192.168.15.43', '80', 'admin', 'Supervisor')

def zeep_pythonvalue(self, xmlvalue):
	return xmlvalue

zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue

# sozdaem servis media objekta cam (objekt cam sozdajetsa pri podkluchenii k kamere)
# servis sozdaetsa 4toby potom poluchit' iz nego profili a iz profiley poluchit' token 4toby dvigat' kameroy
media = cam.create_media_service()

ptz = cam.create_ptz_service()

token = media.GetProfiles()[0].token
print("token", token)

zoomX = ptz.GetStatus(token)['Position']['Zoom']['x']
zoomMultiplier = round(1.01 - zoomX, 2) + 0.85
if zoomMultiplier > 1:
    zoomMultiplier = 1
zoomMultiplierY = round(1.15 - zoomX, 2)
if zoomMultiplierY > 1:
    zoomMultiplierY = 1

req = {'Velocity': {'Zoom': {'space': '', 'x': '0'}, 'PanTilt': {'space': '', 'y': 0, 'x': 0}}, 'ProfileToken': token, 'Timeout': None}

sFrame = video_capture.read()
width = int(sFrame.shape[1])
height = int(sFrame.shape[0])

#widthB = width

#if width == 704:
#    width *= 1.45
safeZx = int(width*0.08)
safeZy = int(height*0.2)

widthSafeL = int(width*0.33)
widthSafeR = int(width*0.66)
heightSafe = int(height*0.5)
widthSafeMin = int(width*0.33 - safeZx)
widthSafeMax = int(width*0.33 + safeZx)
widthSafeMinR = int(width*0.66 - safeZx)
widthSafeMaxR = int(width*0.66 + safeZx)
heightSafeMin = int(height*0.5 - safeZy)
heightSafeMax = int(height*0.5 + safeZy)
a = ((widthSafeMin * 0.2) / (width - widthSafeMax))

def mov_to_face(ptz, request, x, y, width, height, speed_kof = 1, timeout=0):
    if (x >= (widthSafeMinR) and x <= (widthSafeMaxR)):
        request['Velocity']['PanTilt']['x'] = 0
        print("no need to move, right!")
        if (y > heightSafeMin) and (y < heightSafeMax):
            request['Velocity']['PanTilt']['y'] = 0
        elif (y >= heightSafeMax):
            request['Velocity']['PanTilt']['y'] = -1 * zoomMultiplierY * (round(((y - heightSafe) / (height - heightSafe)), 2))
        elif (y <= heightSafeMin):
            request['Velocity']['PanTilt']['y'] = zoomMultiplierY * (round(((heightSafe - y) / heightSafe), 2))
    elif x>widthSafeMaxR:
        request['Velocity']['PanTilt']['x'] = 0.2 * zoomMultiplier * round(((x - widthSafeR) / (width - widthSafeR)), 2)
        print("right = ", request['Velocity']['PanTilt']['x'])
    elif x<widthSafeMinR:
        request['Velocity']['PanTilt']['x'] = a * zoomMultiplier * round((x - widthSafeR) / widthSafeR, 2)
        print("left = ", request['Velocity']['PanTilt']['x'])
    ptz.ContinuousMove(request)
    sleep(timeout)


while True:
    # Grab a single frame of video
    frame = video_capture.read()
    #ret, frame = video_capture.read()
    # Resize frame of video to 1/4 size for faster face detection processing
    try:
        small_frame = imutils.resize(frame,  width=int(width/4))
        #small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    except:
        print("empty frame!")

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(small_frame)
    #face_locations = face_recognition.face_locations(frame)

    print("face locations = ", str(face_locations))
    # Display the results
    for top, right, bottom, left in face_locations:
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Extract the region of the image that contains the face
        #face_image = frame[top:bottom, left:right]

        x = int(left + (right - left) / 2)
        y = int(top + (bottom - top) / 2)
        mov_to_face(ptz, req, x, y, width, height, 0.5, 0)

        # Draw rectangle over the face
        cv2.rectangle(frame, (left, top), (right, bottom), (255,0,0), 2)

    if not face_locations:
        i += 1
    else:
        i = 0

    if i == 10:
        ptz.Stop(token)

    cv2.rectangle(frame, (widthSafeMin, heightSafeMin), (widthSafeMax, heightSafeMax), (0,255,0), 2)
    cv2.rectangle(frame, (widthSafeMinR, heightSafeMin), (widthSafeMaxR, heightSafeMax), (0,255,0), 2)
    #ptz.Stop(token)
    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        ptz.Stop(token)
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()