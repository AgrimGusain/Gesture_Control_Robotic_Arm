#include <ESP32Servo.h>

Servo servo[4];
int default_angle[4] = {75, 90, 90, 45};

// ESP32 PWM pins (adjust these based on your wiring)
const int servo_pins[4] = {18, 19, 21, 22};  // You can use any GPIO pins that support PWM

void setup()
{
    Serial.begin(115200);
    
    // Allow allocation of all timers for ESP32Servo library
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);
     
    // Attach servos to pins
    for (size_t i = 0; i < 4; i++)
    {
        servo[i].setPeriodHertz(50);  // Standard 50hz servo
        servo[i].attach(servo_pins[i], 500, 2400);  // Min/max pulse width in microseconds
        servo[i].write(default_angle[i]);
    }
    
    Serial.println("ESP32 Servo Controller Ready");
}

byte angle[4];
byte pre_angle[4];
unsigned long t = millis();

void loop()
{
    if (Serial.available() >= 4)  // Wait for all 4 bytes
    {
        Serial.readBytes(angle, 4);
        
        for (size_t i = 0; i < 4; i++)
        {
            // Constrain angle to valid servo range (0-180)
            angle[i] = constrain(angle[i], 0, 180);
            
            if (angle[i] != pre_angle[i])
            {
                servo[i].write(angle[i]);
                pre_angle[i] = angle[i];
            }
        }
        t = millis();
    }

    // Timeout: return to default position after 1 second of no data
    if (millis() - t > 1000)
    {
        for (size_t i = 0; i < 4; i++)
        {
            if (pre_angle[i] != default_angle[i])
            {
                servo[i].write(default_angle[i]);
                pre_angle[i] = default_angle[i];
            }
        }
        t = millis();  // Reset timer to avoid continuous writes
    }
}
