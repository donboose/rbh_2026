#include <ESP32Servo.h>

// #define ENABLE_MOTORS 

#define PIN_FL 5   // Front Left
#define PIN_FR 18  // Front Right
#define PIN_RL 19  // Rear Left
#define PIN_RR 15  // Rear Right

float Kp = 1.0;
float Ki = 0.02;
float Kd = 20.0;


Servo ESC_FL, ESC_FR, ESC_RL, ESC_RR;

float errRoll, integralRoll = 0, prevErrRoll = 0;
float errPitch, integralPitch = 0, prevErrPitch = 0;
float errYaw, integralYaw = 0, prevErrYaw = 0;

int throttle = 1000; // Min throttle
float setpointRoll = 0, inputRoll = 0;
float setpointPitch = 0, inputPitch = 0;
float setpointYaw = 0, inputYaw = 0;

float calculatePID(float setpoint, float input, float &prevErr, float &integral) {
  float error = setpoint - input;
  integral += error;
  float derivative = error - prevErr;
  prevErr = error;
  
  integral = constrain(integral, -100, 100); 

  return (Kp * error) + (Ki * integral) + (Kd * derivative);
}

void setup() {
  Serial.begin(115200);
  Serial.println("=== DRONE MIXER & PID TESTER ===");
  Serial.println("Commands:");
  Serial.println("  t <1000-2000>  : Set Throttle");
  Serial.println("  p <angle>      : Set Pitch Error (simulate tilt)");
  Serial.println("  r <angle>      : Set Roll Error");
  Serial.println("  y <angle>      : Set Yaw Error");
  Serial.println("Example: 't 1300' to set throttle, 'p 10' to simulate pitching forward");

  #ifdef ENABLE_MOTORS
    ESC_FL.attach(PIN_FL, 1000, 2000);
    ESC_FR.attach(PIN_FR, 1000, 2000);
    ESC_RL.attach(PIN_RL, 1000, 2000);
    ESC_RR.attach(PIN_RR, 1000, 2000);
    
    Serial.println("Arming ESCs...");
    ESC_FL.writeMicroseconds(1000);
    ESC_FR.writeMicroseconds(1000);
    ESC_RL.writeMicroseconds(1000);
    ESC_RR.writeMicroseconds(1000);
    delay(2000); 
    Serial.println("ESCs Arming Complete (if powered).");
  #else
    Serial.println("MOTORS DISABLED (Safe Mode). Output only to Serial.");
  #endif
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    float val = Serial.parseFloat();
    
    switch(cmd) {
      case 't': throttle = val; break;
      case 'p': inputPitch = val; break;
      case 'r': inputRoll = val; break;
      case 'y': inputYaw = val; break;
    }
    while(Serial.available()) Serial.read(); 
  }

  float pidRoll = calculatePID(0, inputRoll, prevErrRoll, integralRoll);
  float pidPitch = calculatePID(0, inputPitch, prevErrPitch, integralPitch);
  float pidYaw = calculatePID(0, inputYaw, prevErrYaw, integralYaw);

  // Motor Mixing
  // Formula: 
  // FL = Thrust + Roll + Pitch - Yaw
  // FR = Thrust - Roll + Pitch + Yaw
  // RL = Thrust + Roll - Pitch + Yaw
  // RR = Thrust - Roll - Pitch - Yaw
  
  int pwm_FL = throttle + pidRoll + pidPitch + pidYaw; // CW or CCW depending on definition
  int pwm_FR = throttle - pidRoll + pidPitch - pidYaw;
  int pwm_RL = throttle + pidRoll - pidPitch - pidYaw;
  int pwm_RR = throttle - pidRoll - pidPitch + pidYaw;

  // Constrain to ESC limits
  pwm_FL = constrain(pwm_FL, 1000, 2000);
  pwm_FR = constrain(pwm_FR, 1000, 2000);
  pwm_RL = constrain(pwm_RL, 1000, 2000);
  pwm_RR = constrain(pwm_RR, 1000, 2000);
  
  // Safety: If throttle is low, don't spin motors regardless of PID
  if (throttle < 1050) {
    pwm_FL = pwm_FR = pwm_RL = pwm_RR = 1000;
    // Reset integral to prevent accumulation while idle
    integralRoll = integralPitch = integralYaw = 0;
  }

  // Output to Motors
  #ifdef ENABLE_MOTORS
    ESC_FL.writeMicroseconds(pwm_FL);
    ESC_FR.writeMicroseconds(pwm_FR);
    ESC_RL.writeMicroseconds(pwm_RL);
    ESC_RR.writeMicroseconds(pwm_RR);
  #endif

  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 100) {
    Serial.print("Throt:"); Serial.print(throttle);
    Serial.print(" | InPitch:"); Serial.print(inputPitch);
    Serial.print(" | FL:"); Serial.print(pwm_FL);
    Serial.print(" FR:"); Serial.print(pwm_FR);
    Serial.print(" RL:"); Serial.print(pwm_RL);
    Serial.print(" RR:"); Serial.println(pwm_RR);
    lastPrint = millis();
  }
}
