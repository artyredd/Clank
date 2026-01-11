
#define OUT_1 4
#define OUT_2 5


void setup() {
  // put your setup code here, to run once:
  analogReadResolution(12);
  _gpio_init(OUT_1);
  gpio_set_dir(OUT_1, GPIO_OUT);
  _gpio_init(OUT_2);
  gpio_set_dir(OUT_2, GPIO_OUT);
  delay(1000);
}

int halfVcc = 4096>>1;
int vccThr = halfVcc + (4096/10);
int gndThr = halfVcc - (4096/10);

void loop() {
  // put your main code here, to run repeatedly:
  int value = analogRead(28);
  if(value >= vccThr)
  {
    gpio_put(OUT_1, true);
    gpio_put(OUT_2, false);
  }else if( value <= gndThr)
  {
    gpio_put(OUT_2, true);
    gpio_put(OUT_1, false);
  }
  else
  {
    gpio_put(OUT_2, false);
    gpio_put(OUT_1, false);
  }
}
