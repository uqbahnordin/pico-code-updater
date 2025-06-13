import board
import neopixel
import time

# ----- NeoPixel Setup -----
pixel_pin = board.GP1
num_pixels = 12
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.5, auto_write=True)

# ----- Turn All LEDs Yellow -----
yellow = (255, 255, 0)
pixels.fill(yellow)

# Keep the script alive
while True:
    time.sleep(1)
