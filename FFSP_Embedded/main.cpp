#include <Arduino.h>

#define x_acc_pin 14
#define y_acc_pin 16
#define z_acc_pin 17

unsigned long timer = 0;
long loopTime = 100;   // microseconds
unsigned long prev_time = 0;
unsigned long curr_time = 0;

int prev_val1=0;
int prev_val2=0;
int prev_val3=0;

int upper_threshold = 100;
int lower_threshold = 70;
int rising = 1;
int camera_trig = 0;


void timeSync(unsigned long deltaT)
{
  unsigned long currTime = micros();
  long timeToDelay = deltaT - (currTime - timer);
  if (timeToDelay > 5000)
  {
    delay(timeToDelay / 1000);
    delayMicroseconds(timeToDelay % 1000);
  }
  else if (timeToDelay > 0)
  {
    delayMicroseconds(timeToDelay);
  }
  else
  {
      // timeToDelay is negative so we start immediately
  }
  timer = currTime + timeToDelay;
}

void sendToPC(int* data1, int* data2, int* data3, int* data4, int* data5)
{
  byte* byteData1 = (byte*)(data1);
  byte* byteData2 = (byte*)(data2);
  byte* byteData3 = (byte*)(data3);
  byte* byteData4 = (byte*)(data4);
  byte* byteData5 = (byte*)(data5);

  byte buf[10] = {byteData1[0], byteData1[1],
                 byteData2[0], byteData2[1],
                 byteData3[0], byteData3[1],
                 byteData4[0], byteData4[1],
                 byteData5[0], byteData5[1]};
  Serial.write(buf, 10);
}

void sendToPC(double* data1, double* data2, double* data3)
{
  byte* byteData1 = (byte*)(data1);
  byte* byteData2 = (byte*)(data2);
  byte* byteData3 = (byte*)(data3);
  byte buf[12] = {byteData1[0], byteData1[1], byteData1[2], byteData1[3],
                 byteData2[0], byteData2[1], byteData2[2], byteData2[3],
                 byteData3[0], byteData3[1], byteData3[2], byteData3[3]};
  Serial.write(buf, 12);
}

void setup() {
  Serial.begin(2000000);
  timer = micros();
  pinMode(x_acc_pin, INPUT);
  pinMode(y_acc_pin, INPUT);
  pinMode(z_acc_pin, INPUT);
}

void loop() {
  timeSync(loopTime);
  int val1 = analogRead(x_acc_pin) - 512;
  int val2 = analogRead(y_acc_pin) - 512;
  int val3 = analogRead(z_acc_pin) - 512;
  curr_time = micros();
  int delta_t = curr_time - prev_time;
  prev_time = curr_time;

  if( val3 >= upper_threshold && rising == 1){
    camera_trig = 1;
    rising = 0;
  }
  else if( val3 <= lower_threshold && rising == 0){
    camera_trig = 0;
    rising = 1;
  }

  prev_val1 = val1;
  prev_val2 = val2;
  prev_val3 = val3;

  sendToPC(&val1, &val2, &val3, &delta_t, &camera_trig);
}