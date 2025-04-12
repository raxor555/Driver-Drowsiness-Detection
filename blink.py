import cv2
import dlib
import numpy as np
from scipy.spatial import distance as dist
import time
import pygame

pygame.mixer.init()
alarm_sound = pygame.mixer.Sound("crash.wav")

EYE_AR_THRESH = 0.25
CLOSURE_THRESH = 3.0
MIN_BLINK_DURATION = 0.1
MIN_EYE_WIDTH = 20

blink_counter = 0
eye_closed = False
eye_close_start = 0
alarm_playing = False
potential_blink = False
blink_start_time = 0

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

(L_START, L_END) = (36, 42)
(R_START, R_END) = (42, 48)

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    eye_width = dist.euclidean(eye[0], eye[3])
    return ear, eye_width

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        shape = predictor(gray, face)
        shape = np.array([(p.x, p.y) for p in shape.parts()])

        left_eye = shape[L_START:L_END]
        right_eye = shape[R_START:R_END]
        
        left_ear, left_width = eye_aspect_ratio(left_eye)
        right_ear, right_width = eye_aspect_ratio(right_eye)
        
        if left_width > MIN_EYE_WIDTH and right_width > MIN_EYE_WIDTH:
            ear = (left_ear + right_ear) / 2.0
            
            if ear < EYE_AR_THRESH:
                if not eye_closed:
                    eye_close_start = time.time()
                    blink_start_time = time.time()
                    eye_closed = True
                    potential_blink = True
                
                eye_close_duration = time.time() - eye_close_start
                
                if eye_close_duration >= CLOSURE_THRESH and not alarm_playing:
                    alarm_sound.play(-1)
                    alarm_playing = True
            else:
                if eye_closed:
                    if potential_blink and (time.time() - blink_start_time) >= MIN_BLINK_DURATION:
                        blink_counter += 1
                        potential_blink = False
                    
                    eye_closed = False
                    if alarm_playing:
                        alarm_sound.stop()
                        alarm_playing = False
                eye_close_duration = 0

            cv2.putText(frame, f"Blinks: {blink_counter}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if eye_closed:
                blink_duration = time.time() - blink_start_time
                cv2.putText(frame, f"Closed: {eye_close_duration:.1f}s", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                if eye_close_duration >= CLOSURE_THRESH:
                    cv2.putText(frame, "ALERT! EYES CLOSED!", (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.putText(frame, f"EAR: {ear:.2f}", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.polylines(frame, [left_eye], True, (0, 255, 0), 1)
            cv2.polylines(frame, [right_eye], True, (0, 255, 0), 1)
        else:
            cv2.putText(frame, "Eyes not detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Driver Drowsiness Detection", frame)
    if cv2.waitKey(1) == 27:
        if alarm_playing:
            alarm_sound.stop()
        break

cap.release()
cv2.destroyAllWindows()