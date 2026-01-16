#include <Wire.h>
#include <ESP32Servo.h>
#include "MPU9250.h"
#include <MadgwickAHRS.h>


#define PIN_FL 5 
#define PIN_FR 18
#define PIN_RL 19
#define PIN_RR 15

#define MIN_THROTTLE 1050  // Idle speed (must spin motors slowly but reliably)
#define MAX_THROTTLE 1800  // Safety Cap (don't use 2000 yet)
#define BASE_HOVER 1300    // Approximate throttle to hover


float Kp_pitch = 1.3, Ki_pitch = 0.04, Kd_pitch = 18.0;
float Kp_roll  = 1.3, Ki_roll  = 0.04, Kd_roll  = 18.0;
float Kp_yaw   = 3.0, Ki_yaw   = 0.02, Kd_yaw   = 0.0;


MPU9250 mpu;
Madgwick filter;
Servo escFL, escFR, escRL, escRR;

bool isArmed = false;
unsigned long lastLoopTime = 0;
float desiredPitch = 0, desiredRoll = 0, desiredYaw = 0; // Setpoints
int baseThrottle = 1000;

float errPitch, prevErrPitch, iPitch;
float errRoll,  prevErrRoll,  iRoll;
float errYaw,   prevErrYaw,   iYaw;

void resetPID() {
  prevErrPitch = 0; iPitch = 0;
  prevErrRoll = 0;  iRoll = 0;
  prevErrYaw = 0;   iYaw = 0;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  delay(1000);
  if (!mpu.setup(0x68)) {
    Serial.println("MPU Failed!");
    while(1);
  }
  // Optional: mpu.calibrateAccelGyro(); // Do this once and hardcode offsets if possible
  
  filter.begin(250); // Target 250Hz Loop
  
  escFL.attach(PIN_FL, 1000, 2000);
  escFR.attach(PIN_FR, 1000, 2000);
  escRL.attach(PIN_RL, 1000, 2000);
  escRR.attach(PIN_RR, 1000, 2000);
  
  // Send 1000us to arm ESCs
  writeAllMotors(1000);
  
  Serial.println("SYSTEM READY. Send 'A' to Arm, 'D' to Disarm.");
}

void loop() {
  unsigned long currentTime = micros();
  
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'A') {
      isArmed = true;
      resetPID();
      baseThrottle = MIN_THROTTLE;
      Serial.println("ARMED! *** DANGER ***");
    } 
    else if (cmd == 'D') {
      isArmed = false;
      writeAllMotors(1000);
      Serial.println("DISARMED");
    }
    else if (cmd == '+') baseThrottle += 50;
    else if (cmd == '-') baseThrottle -= 50;
  }

  if (currentTime - lastLoopTime >= 4000) {
    float dt = (currentTime - lastLoopTime) / 1000000.0;
    lastLoopTime = currentTime;

    if (mpu.update()) {
      filter.updateIMU(mpu.getGyroX(), mpu.getGyroY(), mpu.getGyroZ(), 
                       mpu.getAccX(),  mpu.getAccY(),  mpu.getAccZ());
    }
    
    float currentPitch = filter.getPitch();
    float currentRoll  = filter.getRoll();

    if (abs(currentPitch) > 45 || abs(currentRoll) > 45) {
      isArmed = false;
      Serial.println("CRASH DETECTED - DISARMING");
    }

    if (!isArmed) {
      writeAllMotors(1000);
      return; 
    }

    errPitch = desiredPitch - currentPitch;
    iPitch  += errPitch * dt;
    iPitch   = constrain(iPitch, -50, 50); // Anti-windup
    float dPitch = (errPitch - prevErrPitch) / dt;
    float pidPitch = (Kp_pitch * errPitch) + (Ki_pitch * iPitch) + (Kd_pitch * dPitch);
    prevErrPitch = errPitch;

    // Roll PID
    errRoll = desiredRoll - currentRoll;
    iRoll  += errRoll * dt;
    iRoll   = constrain(iRoll, -50, 50);
    float dRoll = (errRoll - prevErrRoll) / dt;
    float pidRoll = (Kp_roll * errRoll) + (Ki_roll * iRoll) + (Kd_roll * dRoll);
    prevErrRoll = errRoll;

    // Yaw PID (Simple P-controller for rate damping)
    // For simple hover, we just want to stop spinning
    float pidYaw = 0;

    int m1 = baseThrottle + pidPitch + pidRoll + pidYaw; // FL (CW)
    int m2 = baseThrottle + pidPitch - pidRoll - pidYaw; // FR (CCW)
    int m3 = baseThrottle - pidPitch + pidRoll - pidYaw; // RL (CCW)
    int m4 = baseThrottle - pidPitch - pidRoll + pidYaw; // RR (CW)

    // Constrain to valid range
    m1 = constrain(m1, MIN_THROTTLE, MAX_THROTTLE);
    m2 = constrain(m2, MIN_THROTTLE, MAX_THROTTLE);
    m3 = constrain(m3, MIN_THROTTLE, MAX_THROTTLE);
    m4 = constrain(m4, MIN_THROTTLE, MAX_THROTTLE);

    escFL.writeMicroseconds(m1);
    escFR.writeMicroseconds(m2);
    escRL.writeMicroseconds(m3);
    escRR.writeMicroseconds(m4);
  }
}

void writeAllMotors(int val) {
  escFL.writeMicroseconds(val);
  escFR.writeMicroseconds(val);
  escRL.writeMicroseconds(val);
  escRR.writeMicroseconds(val);
}
