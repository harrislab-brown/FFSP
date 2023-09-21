#include <Arduino.h>

int baud_rate = 115200;

unsigned long timer = 0;
long loopTime = 2000;   // microseconds
unsigned long prev_time = 0;
unsigned long curr_time = 0;

int adc_per_uV = 678;

#define pin_x A0
#define pin_y A1
#define pin_z A2


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


void setup() {
  // put your setup code here, to run once:
   Serial.begin(baud_rate);
   
   //Serial.println("testing in setup!");
  timer = micros();
  pinMode(pin_x, INPUT);
  pinMode(pin_y, INPUT);
  pinMode(pin_z, INPUT);

}

void loop() {
  // put your main code here, to run repeatedly:
  timeSync(loopTime);


  curr_time = micros();
  int delta_t = curr_time - prev_time;
  prev_time = curr_time;
  

  Serial.print((analogRead(pin_x)*adc_per_uV));
  Serial.print(" ");
  Serial.print(analogRead(pin_y)*adc_per_uV);
  Serial.print(" ");
  Serial.print(analogRead(pin_z)*adc_per_uV);
  Serial.print(" ");
  Serial.println(delta_t);
}