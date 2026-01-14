#include <Wire.h>
#include "MPU9250.h"

MPU9250 mpu;

// built in filter

void setup() {
    Serial.begin(115200);
    Wire.begin();       // uses GPIO 21 (SDA), GPIO 22 (SCL) on ESP32
    delay(2000);

    if (!mpu.setup(0x68)) {  // 0x68 if AD0 is grounded
        Serial.println("MPU9250 connection failed!");
        while (1) { delay(1000); }
    }

    // calibrate
    Serial.println("Calibrating gyro and accel... keep sensor still");
    mpu.calibrateAccelGyro();
    Serial.println("Calibrating magnetometer... rotate sensor in figure-8");
    mpu.calibrateMag();
    Serial.println("Calibration done");
}

void loop() {
    if (mpu.update()) {
        // Fused orientation (airplane coords: X-forward, Z-down)
        Serial.print("Yaw: ");   Serial.print(mpu.getYaw());
        Serial.print("  Pitch: "); Serial.print(mpu.getPitch());
        Serial.print("  Roll: ");  Serial.println(mpu.getRoll());

        // Raw sensor data
        Serial.print("AccX: "); Serial.println(mpu.getAccX());
        Serial.print("GyroX: "); Serial.println(mpu.getGyroX());
    }
}
