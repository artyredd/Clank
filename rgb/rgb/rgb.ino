#include "FastLED.h"

/*
  LPD6803,  ///< LPD6803 LED chipset
	LPD8806,  ///< LPD8806 LED chipset
	WS2801,   ///< WS2801 LED chipset
	WS2803,   ///< WS2803 LED chipset
	SM16716,  ///< SM16716 LED chipset
	P9813,    ///< P9813 LED chipset
	APA102,   ///< APA102 LED chipset
	SK9822,   ///< SK9822 LED chipset
	SK9822HD, ///< SK9822 LED chipset with 5-bit gamma correction
	DOTSTAR,  ///< APA102 LED chipset alias
	DOTSTARHD, ///< APA102HD LED chipset alias
	APA102HD, ///< APA102 LED chipset with 5-bit gamma correction
	HD107,  /// Same as APA102, but in turbo 40-mhz mode.
	HD107HD,  /// Same as APA102HD, but in turbo 40-mhz mode.
*/

#define DATA_PIN    0
//#define CLK_PIN   4
#define LED_TYPE    WS2811
#define COLOR_ORDER GRB
#define NUM_LEDS    8
CRGB leds[NUM_LEDS];

#define BRIGHTNESS          128
#define FRAMES_PER_SECOND  120

void setup() {
  delay(3000); // 3 second delay for recovery
  
  // tell FastLED about the LED strip configuration
  FastLED.addLeds<LED_TYPE,DATA_PIN,COLOR_ORDER>(leds, NUM_LEDS).setCorrection(TypicalSMD5050);

  // set master brightness control
  FastLED.setBrightness(BRIGHTNESS);
}

uint8_t gHue = 100; // rotating "base color" used by many of the patterns
  
bool dir = false;

void loop()
{
  // Call the current pattern function once, updating the 'leds' array
  rainbow();
  
  // send the 'leds' array out to the actual LED strip
  FastLED.show();  
  // insert a delay to keep the framerate modest
  FastLED.delay(1000/FRAMES_PER_SECOND); 

  // do some periodic updates
  EVERY_N_MILLISECONDS( 40 ) { 
    if(dir)
    {
      gHue++;
    }
    else
    {
      gHue--;
    }

    if(gHue < 80 || gHue >= 120)
    {
      dir = !dir;
    }
  } // slowly cycle the "base color" through the rainbow
}

// Time scaling factors for each component
#define TIME_FACTOR_HUE 60
#define TIME_FACTOR_SAT 100
#define TIME_FACTOR_VAL 100

void rainbow() 
{
  uint32_t ms = millis();
  
  for(int i = 0; i < NUM_LEDS; i++) {
      // Use different noise functions for each LED and each color component
      uint8_t hue = gHue;//inoise16(ms * TIME_FACTOR_HUE, i * 1000, 0) >> 8;
      //uint8_t sat = inoise16(ms * TIME_FACTOR_SAT, i * 2000, 1000) >> 8;
      uint8_t val = inoise16(ms * TIME_FACTOR_VAL, i * 3000, 2000) >> 8;
      
      // Map the noise to full range for saturation and value
      //sat = 255;//map(sat, 0, 255, 30, 255);
      val = map(val, 0, 255, 100, 255);
      
      leds[i] = CHSV(hue, 255, val);
  }
}