import cv2
import numpy as np
import time
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Initialize MediaPipe Hand Landmarker
base_options = python.BaseOptions(model_asset_path='../hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)
landmarker = vision.HandLandmarker.create_from_options(options)

# Gesture tracking variables
cooldown_time = 1.0  # Seconds between gestures
last_gesture_time = 0
last_gesture_type = None


def on():
    """Function called when showing OPEN HAND"""
    print("🟢 ON - Open Hand")
    # Add your custom action here


def off():
    """Function called when showing CLOSED FIST"""
    print("🔴 OFF - Closed Fist")
    # Add your custom action here


def count_fingers(hand_landmarks):
    """
    Count extended fingers
    Returns: number of extended fingers (0-5)
    """
    fingers_up = 0
    
    # Thumb: Check if thumb tip is farther from wrist than thumb IP joint
    if hand_landmarks[4].x < hand_landmarks[3].x:  # For right hand
        fingers_up += 1
    elif hand_landmarks[4].x > hand_landmarks[3].x:  # For left hand (reversed)
        fingers_up += 1
    
    # Index finger: tip vs PIP joint
    if hand_landmarks[8].y < hand_landmarks[6].y:
        fingers_up += 1
    
    # Middle finger
    if hand_landmarks[12].y < hand_landmarks[10].y:
        fingers_up += 1
    
    # Ring finger
    if hand_landmarks[16].y < hand_landmarks[14].y:
        fingers_up += 1
    
    # Pinky
    if hand_landmarks[20].y < hand_landmarks[18].y:
        fingers_up += 1
    
    return fingers_up


def detect_gesture(hand_landmarks, current_time):
    """
    Detect hand open (5 fingers) or closed fist (0-1 fingers)
    Returns: 'open', 'closed', or None
    """
    global last_gesture_time, last_gesture_type
    
    if hand_landmarks is None:
        return None
    
    # Check cooldown
    if current_time - last_gesture_time < cooldown_time:
        return None
    
    fingers = count_fingers(hand_landmarks)
    
    # Open hand - 4 or 5 fingers extended
    if fingers >= 4 and last_gesture_type != 'open':
        last_gesture_time = current_time
        last_gesture_type = 'open'
        return 'open'
    
    # Closed fist - 0 or 1 finger
    elif fingers <= 1 and last_gesture_type != 'closed':
        last_gesture_time = current_time
        last_gesture_type = 'closed'
        return 'closed'
    
    return None


def draw_landmarks_on_image(frame, detection_result):
    """Draw hand landmarks on the image"""
    if not detection_result.hand_landmarks:
        return frame
    
    # Hand landmark connections (simplified)
    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),  # Index finger
        (0, 17), (5, 9), (9, 10), (10, 11), (11, 12),  # Middle finger
        (9, 13), (13, 14), (14, 15), (15, 16),  # Ring finger
        (13, 17), (17, 18), (18, 19), (19, 20),  # Pinky
    ]
    
    for hand_landmarks in detection_result.hand_landmarks:
        h, w, _ = frame.shape
        
        # Draw connections
        for connection in HAND_CONNECTIONS:
            start_idx = connection[0]
            end_idx = connection[1]
            
            if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                start_landmark = hand_landmarks[start_idx]
                end_landmark = hand_landmarks[end_idx]
                
                start_point = (int(start_landmark.x * w), int(start_landmark.y * h))
                end_point = (int(end_landmark.x * w), int(end_landmark.y * h))
                
                cv2.line(frame, start_point, end_point, (0, 255, 0), 2)
        
        # Draw landmarks
        for landmark in hand_landmarks:
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            cv2.circle(frame, (cx, cy), 7, (255, 255, 255), 1)
    
    return frame


def main():
    """Main function to run gesture control"""
    global last_gesture_time
    cap = cv2.VideoCapture(0)
    
    print("Hand Gesture Control Started!")
    print("OPEN HAND (5 fingers) to turn ON")
    print("CLOSED FIST (0 fingers) to turn OFF")
    print("Press 'q' to quit\n")
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Failed to capture frame")
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        frame_height, frame_width, _ = frame.shape
        
        current_time = time.time()
        
        # Convert frame to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Detect hand landmarks
        detection_result = landmarker.detect(mp_image)
        
        hand_landmarks = None
        fingers_count = 0
        if detection_result.hand_landmarks:
            hand_landmarks = detection_result.hand_landmarks[0]
            fingers_count = count_fingers(hand_landmarks)
            
            # Draw landmarks on frame
            frame = draw_landmarks_on_image(frame, detection_result)
            
            # Draw finger count
            cv2.putText(frame, f"Fingers: {fingers_count}", (10, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 3)
        
        # Draw gesture instructions with icons
        # Open hand icon area
        cv2.rectangle(frame, (10, 130), (200, 230), (0, 255, 0), 2)
        cv2.putText(frame, "OPEN HAND", (20, 160),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, "= ON", (60, 210),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Closed fist icon area
        cv2.rectangle(frame, (frame_width - 200, 130), (frame_width - 10, 230), (0, 0, 255), 2)
        cv2.putText(frame, "CLOSED FIST", (frame_width - 190, 160),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(frame, "= OFF", (frame_width - 130, 210),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Detect gesture
        gesture = detect_gesture(hand_landmarks, current_time)
        
        # Show cooldown timer
        time_since_last = current_time - last_gesture_time
        if time_since_last < cooldown_time:
            remaining = cooldown_time - time_since_last
            cv2.putText(frame, f"Wait: {remaining:.1f}s", (frame_width - 180, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        
        if gesture == 'open':
            on()
            cv2.rectangle(frame, (0, 0), (frame_width, frame_height), (0, 255, 0), 10)
            cv2.putText(frame, "ON - OPEN HAND", (frame_width//2 - 200, frame_height//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 4)
        elif gesture == 'closed':
            off()
            cv2.rectangle(frame, (0, 0), (frame_width, frame_height), (0, 0, 255), 10)
            cv2.putText(frame, "OFF - CLOSED FIST", (frame_width//2 - 220, frame_height//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
        
        # Display instructions
        cv2.putText(frame, "Show OPEN HAND or CLOSED FIST to control", 
                   (10, frame_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow('Hand Gesture Control', frame)
        
        # Quit on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    print("\nGesture control stopped.")


if __name__ == "__main__":
    main()
