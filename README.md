# Hand Gesture Controlled Robotic Arm
## MediaPipe 0.10.32 Version

This project uses MediaPipe 0.10.32 hand tracking to control a robotic arm with 4 servos via ESP32.

## 🎯 Features
- Real-time hand tracking using MediaPipe 0.10.32
- Automatic model download on first run
- 4-axis servo control (X, Y, Z, Claw)
- Fist detection for claw control
- Video recording capability
- Debug mode for testing without hardware

## 📋 Hardware Requirements
- ESP32 development board
- 4 servo motors (SG90 or similar)
- USB cable for ESP32
- Camera (USB webcam or phone via IP Webcam app)
- Power supply for servos (5V recommended)

## 🔌 Wiring

Connect servos to ESP32 GPIO pins:
- **Servo 0 (X-axis)**: GPIO 18
- **Servo 1 (Y-axis)**: GPIO 19
- **Servo 2 (Z-axis)**: GPIO 21
- **Servo 3 (Claw)**: GPIO 22

**Important:** Servos should have their own power supply. Connect:
- Servo signal wires → ESP32 GPIO pins
- Servo power (VCC) → External 5V supply
- Servo ground (GND) → Common ground with ESP32

## 🔧 ESP32 Setup

### 1. Install Arduino IDE and ESP32 Support

1. Download and install [Arduino IDE](https://www.arduino.cc/en/software)

2. Add ESP32 board support:
   - Open Arduino IDE
   - Go to **File → Preferences**
   - Add to "Additional Board Manager URLs":
     ```
     https://dl.espressif.com/dl/package_esp32_index.json
     ```
   - Go to **Tools → Board → Boards Manager**
   - Search for "ESP32"
   - Install "**esp32 by Espressif Systems**"

### 2. Install ESP32Servo Library

1. Go to **Sketch → Include Library → Manage Libraries**
2. Search for "**ESP32Servo**"
3. Install "**ESP32Servo by Kevin Harrington**"

### 3. Upload Code to ESP32

1. Open `esp32_servo_controller.ino` in Arduino IDE
2. Select your board: **Tools → Board → ESP32 Arduino → ESP32 Dev Module** (or your specific board)
3. Select the COM port: **Tools → Port → COM# (ESP32)**
4. Click **Upload** button
5. Wait for "Done uploading" message

## 🐍 Python Setup

### 1. Install Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Settings

Edit `main.py` to configure:

```python
# Line 11-12: Set debug mode and camera source
debug = True  # Set to False when ready to connect to ESP32
cam_source = 0  # 0 for USB webcam, "http://192.168.1.100:4747/video" for IP webcam

# Line 15: Set serial port (when debug = False)
ser = serial.Serial('COM4', 115200)  # Change COM4 to your ESP32's port
# Windows: 'COM3', 'COM4', etc.
# Linux: '/dev/ttyUSB0', '/dev/ttyACM0'
# Mac: '/dev/cu.usbserial-XXXX'
```

### 3. Run the Application

```bash
python main.py
```

On **first run**, the script will automatically download the MediaPipe hand tracking model (~26 MB). This only happens once.

## 🎮 How to Use

### Hand Controls:
- **X-axis (Servo 0)**: Hand rotation (angle between wrist and index finger)
- **Y-axis (Servo 1)**: Hand vertical position (up/down)
- **Z-axis (Servo 2)**: Hand distance from camera (forward/backward)
- **Claw (Servo 3)**: 
  - Open hand = Claw opens
  - Make a fist = Claw closes

### Keyboard Controls:
- **ESC key**: Exit the program

### Tips:
1. Show **only ONE hand** in the camera view
2. Ensure **good lighting** for better detection
3. Keep hand **clearly visible** to the camera
4. Start in **debug mode** to test without hardware

## 🔍 Troubleshooting

### Model Download Issues
**Problem:** Model fails to download automatically

**Solution:**
- Download manually from: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
- Save as `hand_landmarker.task` in the same folder as `main.py`

### Camera Not Working
**Problem:** "Cannot open camera source" error

**Solutions:**
- Try different camera sources: `cam_source = 0`, `1`, or `2`
- For IP Webcam app: ensure phone and PC are on same network
- Check camera permissions
- Test camera with another app first

### ESP32 Not Found
**Problem:** Arduino IDE doesn't show ESP32 port

**Solutions:**
- Install CP2102 or CH340 USB drivers (depends on your ESP32)
- Try a different USB cable (must be data cable, not charging-only)
- Press the BOOT button on ESP32 while uploading
- Check Device Manager (Windows) to see if device is recognized

### Hand Not Detected
**Problem:** No hand landmarks shown

**Solutions:**
- Improve lighting conditions
- Move hand closer to camera
- Ensure hand is clearly visible with fingers spread
- Adjust `min_hand_detection_confidence` in code (lower = more sensitive)

### Servos Not Responding
**Problem:** Servos don't move when hand gestures are detected

**Solutions:**
1. Verify debug mode is OFF: `debug = False`
2. Check serial port is correct
3. Verify ESP32 is powered and code is uploaded
4. Check servo wiring and power supply
5. Open Arduino Serial Monitor (115200 baud) to see if ESP32 is receiving data

### Jerky/Unstable Movement
**Problem:** Servos move erratically

**Solutions:**
- Add smoothing by adjusting detection thresholds
- Use external power supply for servos (ESP32 can't power servos)
- Check servo connections
- Reduce `min_tracking_confidence` for smoother tracking

## 📝 Configuration Options

### Servo Angle Ranges (in `main.py`):
```python
x_min, x_mid, x_max = 0, 75, 150
y_min, y_mid, y_max = 0, 90, 180
z_min, z_mid, z_max = 10, 90, 180
claw_open_angle, claw_close_angle = 60, 0
```

### Hand Detection Ranges:
```python
palm_angle_min, palm_angle_mid = -50, 20
wrist_y_min, wrist_y_max = 0.3, 0.9
palm_size_min, palm_size_max = 0.1, 0.3
```

### Fist Detection Sensitivity:
```python
fist_threshold = 7  # Lower = easier to trigger, Higher = harder to trigger
```

## 🔒 Safety Notes

⚠️ **Important Safety Guidelines:**
- Always test servos individually before assembly
- Use appropriate power supply (5V, 2A+ for multiple servos)
- Keep fingers away from moving parts
- Add physical limits/stoppers to prevent over-rotation
- The system returns to default position after 1 second of no data
- Start with `debug = True` to test safely without hardware

## 📊 System Information

- **MediaPipe Version**: 0.10.32 (Tasks API)
- **Model**: Hand Landmarker (Float16)
- **Python**: 3.8+
- **OpenCV**: 4.7.0.68
- **Serial**: pyserial 3.5

## 🆘 Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all connections and settings
3. Test components individually (camera, ESP32, servos)
4. Check that model file exists: `hand_landmarker.task`
5. Review console output for error messages

## 📄 Files Included

- `main.py` - Main Python application (MediaPipe 0.10.32)
- `esp32_servo_controller.ino` - ESP32 Arduino code
- `requirements.txt` - Python dependencies
- `README.md` - This file

## 🎓 Learning Resources

- [MediaPipe Hand Landmarker](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker)
- [ESP32 Arduino Documentation](https://docs.espressif.com/projects/arduino-esp32/)
- [ESP32Servo Library](https://github.com/madhephaestus/ESP32Servo)

---

**Enjoy your hand-controlled robotic arm! 🤖✋**