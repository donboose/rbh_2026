#include <Wire.h>
#include "MPU9250.h"

// add filter

MPU9250 IMU(Wire, 0x68);  // I2C bus, address 0x68

void setup() {
    Serial.begin(115200);
    Wire.begin(21, 22);  // SDA = 21, SCL = 22

    int status = IMU.begin();
    if (status < 0) {
        Serial.print("IMU init failed, status: ");
        Serial.println(status);
        while (1) {}
    }

    IMU.setAccelRange(MPU9250::ACCEL_RANGE_8G);
    IMU.setGyroRange(MPU9250::GYRO_RANGE_500DPS);
    IMU.setDlpfBandwidth(MPU9250::DLPF_BANDWIDTH_41HZ);
    IMU.setSrd(9);  // 1000/(1+9) = 100 Hz output rate
}

void loop() {
    IMU.readSensor();

    Serial.print("AccX: "); Serial.print(IMU.getAccelX_mss());
    Serial.print("  AccY: "); Serial.print(IMU.getAccelY_mss());
    Serial.print("  AccZ: "); Serial.println(IMU.getAccelZ_mss());

    Serial.print("GyroX: "); Serial.print(IMU.getGyroX_rads());
    Serial.print("  GyroY: "); Serial.print(IMU.getGyroY_rads());
    Serial.print("  GyroZ: "); Serial.println(IMU.getGyroZ_rads());

    Serial.print("MagX: "); Serial.print(IMU.getMagX_uT());
    Serial.print("  MagY: "); Serial.print(IMU.getMagY_uT());
    Serial.print("  MagZ: "); Serial.println(IMU.getMagZ_uT());

    delay(10);
}
