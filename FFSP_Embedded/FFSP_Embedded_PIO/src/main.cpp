#include <Arduino.h>

#define x_acc_pin 14
#define y_acc_pin 16
#define z_acc_pin 17

uint16_t sample_period = 100;   // microseconds

uint32_t prev_time = 0;
uint32_t curr_time = 0;
uint32_t next_time = 0;




void timeSync(unsigned long deltaT)
// Dynamic delay function that keeps program running on a consistent timer loop. 
// changed delay amount based on how long previous runtime loop took to run
{
  unsigned long currTime = micros();
  long timeToDelay = deltaT - (currTime - next_time);
  if (timeToDelay > 5000){
    delay(timeToDelay / 1000);
    delayMicroseconds(timeToDelay % 1000);
  }
  else if (timeToDelay > 0){
    delayMicroseconds(timeToDelay);
  }
  else{
      // timeToDelay is negative so we start immediately
  }
  next_time = currTime + timeToDelay;
}

void sendToPc(int16_t* data){
  byte* byteData = (byte*)(data);
  Serial.write(byteData, 2);
}

void sendToPC(int* data1, int* data2, int* data3, int* data4)
{
  byte* byteData1 = (byte*)(data1);
  byte* byteData2 = (byte*)(data2);
  byte* byteData3 = (byte*)(data3);
  byte* byteData4 = (byte*)(data4);

  byte buf[8] = {byteData1[0], byteData1[1],
                 byteData2[0], byteData2[1],
                 byteData3[0], byteData3[1],
                 byteData4[0], byteData4[1]};
  Serial.write(buf, 8);
}

void setup() {
  Serial.begin(2000000);
  next_time = micros();
  pinMode(x_acc_pin, INPUT);
  pinMode(y_acc_pin, INPUT);
  pinMode(z_acc_pin, INPUT);
}

void loop() {

  // check for user input, update sample period
  if (Serial.available() > 0){
    sample_period = Serial.parseInt();
  }

  timeSync(sample_period);
  curr_time = micros();
  int delta_t = curr_time - prev_time;
  prev_time = curr_time;

  int16_t z_accel = analogRead(z_acc_pin);
  sendToPc(&z_accel);
}
