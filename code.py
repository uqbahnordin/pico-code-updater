import board
import neopixel
import time
import wifi
import socketpool
import microcontroller
from adafruit_httpserver.server import Server
from adafruit_httpserver.request import Request
from adafruit_httpserver.response import Response
from adafruit_httpserver.methods import GET
from secrets import secrets

# ----- NeoPixel Setup -----
pixel_pin = board.GP1
num_pixels = 12
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.5, auto_write=False)

# ----- Animation: Blue running light during connection -----
def show_connecting_animation():
    for i in range(12):
        pixels.fill((0, 0, 0))
        pixels[i % num_pixels] = (0, 0, 255)
        pixels.show()
        time.sleep(0.05)

# ----- Animation: Green blink twice for connection success -----
def show_connected_feedback():
    for _ in range(2):
        pixels.fill((0, 255, 0))
        pixels.show()
        time.sleep(0.3)
        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(0.3)

# ----- Wi-Fi Connect -----
print("Connecting to Wi-Fi...")
while not wifi.radio.connected:
    show_connecting_animation()
    try:
        wifi.radio.connect(secrets["ssid"], secrets["password"])
    except:
        pass
print("Connected to", secrets["ssid"])
print("IP address:", wifi.radio.ipv4_address)
show_connected_feedback()

# ----- Web Server Setup -----
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)

# ----- State Variables -----
current_color = (255, 0, 0)
brightness_values = [0.1, 0.2, 0.4, 0.7, 1.0]
brightness_level = 3
brightness_direction = 1
auto_brightness = False
running_mode = False
run_index = 0
last_change = time.monotonic()

# ----- HTML Page -----
html = """
<!DOCTYPE html>
<html>
<head>
    <title>NeoPixel Control</title>
    <style>
        body {
            font-size: 24px;
            font-family: sans-serif;
            text-align: center;
            padding: 20px;
        }
        button {
            font-size: 24px;
            padding: 10px 20px;
            margin: 10px;
        }
    </style>
</head>
<body>
    <h1>Control NeoPixel</h1>

    <h2>Colors</h2>
    <a href="/?color=red"><button>Red</button></a>
    <a href="/?color=green"><button>Green</button></a>
    <a href="/?color=blue"><button>Blue</button></a>
    <a href="/?color=yellow"><button>Yellow</button></a>
    <a href="/?color=off"><button>Off</button></a>

    <h2>Brightness</h2>
    <a href="/?brightness=1"><button>Level 1</button></a>
    <a href="/?brightness=2"><button>Level 2</button></a>
    <a href="/?brightness=3"><button>Level 3</button></a>
    <a href="/?brightness=4"><button>Level 4</button></a>
    <a href="/?brightness=5"><button>Level 5</button></a>

    <h2>Auto Brightness</h2>
    <a href="/start"><button>Start</button></a>
    <a href="/stop"><button>Stop</button></a>

    <h2>Running Mode</h2>
    <a href="/runstart"><button>Start Running</button></a>
    <a href="/runstop"><button>Stop Running</button></a>
</body>
</html>
"""

# ----- Route Handlers -----
@server.route("/", GET)
def handle_root(request: Request):
    global current_color, brightness_level, auto_brightness, running_mode

    color = request.query_params.get("color")
    brightness = request.query_params.get("brightness")

    if color:
        auto_brightness = False
        running_mode = False
        if color == "red":
            current_color = (255, 0, 0)
        elif color == "green":
            current_color = (0, 255, 0)
        elif color == "blue":
            current_color = (0, 0, 255)
        elif color == "yellow":
            current_color = (255, 255, 0)
        elif color == "off":
            current_color = (0, 0, 0)
        pixels.fill(current_color)
        pixels.show()

    if brightness:
        auto_brightness = False
        running_mode = False
        try:
            brightness_level = max(1, min(5, int(brightness)))
            pixels.brightness = brightness_values[brightness_level - 1]
            pixels.fill(current_color)
            pixels.show()
        except:
            pass

    return Response(request, html, content_type="text/html")

@server.route("/start", GET)
def handle_start(request: Request):
    global auto_brightness, running_mode
    auto_brightness = True
    running_mode = False
    return Response(request, html, content_type="text/html")

@server.route("/stop", GET)
def handle_stop(request: Request):
    global auto_brightness, running_mode
    auto_brightness = False
    running_mode = False
    return Response(request, html, content_type="text/html")

@server.route("/runstart", GET)
def handle_runstart(request: Request):
    global running_mode, auto_brightness
    running_mode = True
    auto_brightness = False
    return Response(request, html, content_type="text/html")

@server.route("/runstop", GET)
def handle_runstop(request: Request):
    global running_mode
    running_mode = False
    return Response(request, html, content_type="text/html")

# ----- Start Server -----
server.start(str(wifi.radio.ipv4_address))
print("Web server started.")

# ----- Main Loop -----
while True:
    try:
        server.poll()
        now = time.monotonic()

        if auto_brightness and now - last_change > 0.5:
            last_change = now
            pixels.brightness = brightness_values[brightness_level - 1]
            pixels.fill(current_color)
            pixels.show()
            brightness_level += brightness_direction
            if brightness_level == 5:
                brightness_direction = -1
            elif brightness_level == 1:
                brightness_direction = 1

        if running_mode and now - last_change > 0.1:
            last_change = now
            pixels.fill((0, 0, 0))
            pixels[run_index % num_pixels] = current_color
            pixels.show()
            run_index += 1

    except Exception as e:
        print("Error:", e)
        microcontroller.reset()
