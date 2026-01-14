#include "MPU9250.h"
#include <MadgwickAHRS.h>

MPU9250 mpu;
Madgwick filter;

unsigned long microsPerReading, microsPrevious;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  delay(2000);

  // Initialize MPU9250
  if (!mpu.setup(0x68)) {
      Serial.println("MPU connection failed. Please check your wiring.");
      while (1) delay(1000);
  }

  // Calibrate 
  Serial.println("Calibrating IMU... Keep still.");
  mpu.calibrateAccelGyro();
  Serial.println("Magnetometer calibration... Wave in figure-8.");
  mpu.calibrateMag();
  Serial.println("Calibration done!");

  // Start the filter
  filter.begin(50); // 50 Hz
  microsPerReading = 1000000 / 50;
  microsPrevious = micros();
}

void loop() {
  unsigned long microsNow = micros();
  
  if (microsNow - microsPrevious >= microsPerReading) {
    
    if (mpu.update()) {
      float ax = mpu.getAccX();
      float ay = mpu.getAccY();
      float az = mpu.getAccZ();
      float gx = mpu.getGyroX();
      float gy = mpu.getGyroY();
      float gz = mpu.getGyroZ();
      float mx = mpu.getMagX();
      float my = mpu.getMagY();
      float mz = mpu.getMagZ();

      // Update Madgwick Filter
      // Note: Madgwick library expects Gyro in Degrees/Sec, Accel in G, Mag in uT.
      // (The hideakitai library returns these units by default)
      // Use 9DOF (includes Magnetometer) for Yaw stability
      filter.update(gx, gy, gz, ax, ay, az, mx, my, mz);
      // OR: Use 6DOF (Gyro + Accel only) if Magnetometer is noisy/uncalibrated
      // filter.updateIMU(gx, gy, gz, ax, ay, az);

      float roll = filter.getRoll();
      float pitch = filter.getPitch();
      float yaw = filter.getYaw();

      Serial.print("Roll:");
      Serial.print(roll);
      Serial.print(",");
      Serial.print("Pitch:");
      Serial.print(pitch);
      Serial.print(",");
      Serial.print("Yaw:");
      Serial.println(yaw);
    }
    
    microsPrevious = microsPrevious + microsPerReading;
  }
}
