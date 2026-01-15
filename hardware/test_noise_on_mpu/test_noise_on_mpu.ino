#include <Wire.h>
#include "MPU9250.h"
#include <ESP32Servo.h>

MPU9250 mpu;
Servo esc[4];
// Pins: FL, FR, RL, RR
int pins[] = {5, 18, 19, 15}; 

void setup() {
    Serial.begin(115200);
    Wire.begin();
    mpu.setup(0x68);
    
    // Init ESCs
    for(int i=0; i<4; i++) {
        esc[i].attach(pins[i], 1000, 2000);
        esc[i].writeMicroseconds(1000); // Arm
    }
    delay(2000);
}

void loop() {
    if (Serial.available()) {
        int val = Serial.parseInt();
        // Safety cap at 1500 (50%) for testing
        val = constrain(val, 1000, 1500); 
        for(int i=0; i<4; i++) esc[i].writeMicroseconds(val);
    }
    
    if (mpu.update()) {
        // Plot raw accelerometer data
        Serial.print("Ax:"); Serial.print(mpu.getAccX());
        Serial.print(" Ay:"); Serial.print(mpu.getAccY());
        Serial.print(" Az:"); Serial.println(mpu.getAccZ());
    }
}
