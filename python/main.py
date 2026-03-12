import serial
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os
import urllib.request

# config
write_video = False
debug = False
cam_source = 0  # 0,1 for usb cam, "http://192.168.1.100:4747/video" for IP webcam

if not debug:
    ser = serial.Serial('COM9', 115200)

x_min = 0
x_mid = 75
x_max = 150
# use angle between wrist and index finger to control x axis
palm_angle_min = -50
palm_angle_mid = 20

y_min = 0
y_mid = 90
y_max = 180
# use wrist y to control y axis
wrist_y_min = 0.3
wrist_y_max = 0.9

z_min = 10
z_mid = 90
z_max = 180
# use palm size to control z axis
palm_size_min = 0.1
palm_size_max = 0.3

claw_open_angle = 20
claw_close_angle = 140

servo_angle = [x_mid, y_mid, z_mid, claw_open_angle]  # [x, y, z, claw]
prev_servo_angle = servo_angle.copy()
fist_threshold = 7

clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
map_range = lambda x, in_min, in_max, out_min, out_max: abs((x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min)


# Download model if not present
def download_model():
    model_path = 'hand_landmarker.task'
    if not os.path.exists(model_path):
        print("Downloading hand landmarker model... (This may take a minute)")
        url = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
        try:
            urllib.request.urlretrieve(url, model_path)
            print("Model downloaded successfully!")
        except Exception as e:
            print(f"Error downloading model: {e}")
            print("Please download manually from:")
            print("https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")
            print("and save it as 'hand_landmarker.task' in the same folder as this script.")
            exit(1)
    return model_path


# Check if the hand is a fist
def is_fist(hand_landmarks, palm_size):
    """Calculate if hand is in fist position based on finger distances from wrist"""
    distance_sum = 0
    WRIST = hand_landmarks[0]
    # Check knuckles and fingertips
    for i in [7, 8, 11, 12, 15, 16, 19, 20]:
        distance_sum += ((WRIST.x - hand_landmarks[i].x)**2 +
                         (WRIST.y - hand_landmarks[i].y)**2 +
                         (WRIST.z - hand_landmarks[i].z)**2)**0.5
    return distance_sum / palm_size < fist_threshold


def landmark_to_servo_angle(hand_landmarks):
    """Convert hand landmarks to servo angles"""
    servo_angle = [x_mid, y_mid, z_mid, claw_open_angle]
    WRIST = hand_landmarks[0]
    INDEX_FINGER_MCP = hand_landmarks[5]
    
    # Calculate palm size (distance between wrist and index finger base)
    palm_size = ((WRIST.x - INDEX_FINGER_MCP.x)**2 +
                 (WRIST.y - INDEX_FINGER_MCP.y)**2 +
                 (WRIST.z - INDEX_FINGER_MCP.z)**2)**0.5

    # Control claw based on fist detection
    if is_fist(hand_landmarks, palm_size):
        servo_angle[3] = claw_close_angle
    else:
        servo_angle[3] = claw_open_angle

    # Calculate X angle (hand rotation)
    distance = palm_size
    if distance > 0:  # Avoid division by zero
        angle = (WRIST.x - INDEX_FINGER_MCP.x) / distance
        angle = int(angle * 180 / 3.1415926)
        angle = clamp(angle, palm_angle_min, palm_angle_mid)
        servo_angle[0] = map_range(angle, palm_angle_min, palm_angle_mid, x_max, x_min)

    # Calculate Y angle (hand vertical position)
    wrist_y = clamp(WRIST.y, wrist_y_min, wrist_y_max)
    servo_angle[1] = map_range(wrist_y, wrist_y_min, wrist_y_max, y_max, y_min)

    # Calculate Z angle (hand distance from camera)
    palm_size = clamp(palm_size, palm_size_min, palm_size_max)
    servo_angle[2] = map_range(palm_size, palm_size_min, palm_size_max, z_max, z_min)

    # Convert to integers
    servo_angle = [int(i) for i in servo_angle]

    return servo_angle


def draw_landmarks_on_image(rgb_image, detection_result):
    """Draw hand landmarks and connections on the image"""
    annotated_image = np.copy(rgb_image)
    
    if not detection_result.hand_landmarks:
        return annotated_image
    
    # Hand landmark connections (MediaPipe hand model)
    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),          # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),          # Index finger
        (0, 9), (9, 10), (10, 11), (11, 12),     # Middle finger
        (0, 13), (13, 14), (14, 15), (15, 16),   # Ring finger
        (0, 17), (17, 18), (18, 19), (19, 20),   # Pinky
        (5, 9), (9, 13), (13, 17)                # Palm
    ]
    
    # Draw for each detected hand
    for hand_landmarks in detection_result.hand_landmarks:
        # Draw connections first (so they appear behind landmarks)
        for connection in connections:
            start_idx, end_idx = connection
            start = hand_landmarks[start_idx]
            end = hand_landmarks[end_idx]
            
            start_point = (int(start.x * rgb_image.shape[1]), 
                          int(start.y * rgb_image.shape[0]))
            end_point = (int(end.x * rgb_image.shape[1]), 
                        int(end.y * rgb_image.shape[0]))
            
            cv2.line(annotated_image, start_point, end_point, (0, 255, 0), 2)
        
        # Draw landmarks on top
        for landmark in hand_landmarks:
            x = int(landmark.x * rgb_image.shape[1])
            y = int(landmark.y * rgb_image.shape[0])
            cv2.circle(annotated_image, (x, y), 5, (255, 0, 0), -1)
            cv2.circle(annotated_image, (x, y), 5, (0, 0, 255), 2)
    
    return annotated_image


def main():
    global servo_angle, prev_servo_angle
    
    # Download model if needed
    model_path = download_model()
    
    # Create HandLandmarker
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    detector = vision.HandLandmarker.create_from_options(options)
    
    # Open camera
    cap = cv2.VideoCapture(cam_source)
    
    if not cap.isOpened():
        print(f"Error: Cannot open camera source: {cam_source}")
        exit(1)
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Video writer
    out = None
    if write_video:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('output.avi', fourcc, 30.0, (640, 480))
    
    print("=" * 50)
    print("Hand Gesture Controlled Robotic Arm")
    print("=" * 50)
    print("Controls:")
    print("  - Show one hand to control the arm")
    print("  - Make a fist to close the claw")
    print("  - Open hand to open the claw")
    print("  - Press ESC to exit")
    print("=" * 50)
    
    frame_count = 0
    
    try:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Warning: Empty camera frame")
                continue
            
            frame_count += 1
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Create MediaPipe Image object
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
            
            # Detect hand landmarks
            detection_result = detector.detect(mp_image)
            
            # Draw hand landmarks
            annotated_image = draw_landmarks_on_image(rgb_image, detection_result)
            annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
            
            # Process hand gestures
            if detection_result.hand_landmarks:
                num_hands = len(detection_result.hand_landmarks)
                
                if num_hands == 1:
                    # Single hand detected - control the arm
                    hand_landmarks = detection_result.hand_landmarks[0]
                    servo_angle = landmark_to_servo_angle(hand_landmarks)
                    
                    # Send to Arduino if changed
                    if servo_angle != prev_servo_angle:
                        print(f"Servo angles: X={servo_angle[0]:3d}° Y={servo_angle[1]:3d}° Z={servo_angle[2]:3d}° Claw={servo_angle[3]:3d}°")
                        prev_servo_angle = servo_angle.copy()
                        
                        if not debug:
                            try:
                                ser.write(bytearray(servo_angle))
                            except Exception as e:
                                print(f"Serial communication error: {e}")
                else:
                    # Multiple hands detected
                    if frame_count % 30 == 0:  # Print every 30 frames to avoid spam
                        print(f"Warning: {num_hands} hands detected. Show only one hand.")
            
            # Flip image horizontally for mirror view
            annotated_image = cv2.flip(annotated_image, 1)
            
            # Display servo angles on screen
            text = f"X:{servo_angle[0]} Y:{servo_angle[1]} Z:{servo_angle[2]} Claw:{servo_angle[3]}"
            cv2.putText(annotated_image, text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
            
            # Display mode indicator
            mode_text = "DEBUG MODE" if debug else "CONNECTED TO ARDUINO"
            cv2.putText(annotated_image, mode_text, (10, 460), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
            
            # Show the image
            cv2.imshow('Hand Gesture Control', annotated_image)
            
            # Write video if enabled
            if write_video and out is not None:
                out.write(annotated_image)
            
            # Check for ESC key
            if cv2.waitKey(5) & 0xFF == 27:
                print("\nExiting...")
                break
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        # Cleanup
        cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()
        if not debug:
            ser.close()
        print("Cleanup complete. Goodbye!")


if __name__ == "__main__":
    main()