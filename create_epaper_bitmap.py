import sys
import os
import json
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd4in26

# Example JSON data (replace with actual data source)
buses_json = '''[
    {"number": "444", "destination": "Slussen", "minutes": 5},
    {"number": "471", "destination": "Slussen", "time": "14:30"},
    {"number": "445", "destination": "Slussen", "minutes": 12}
]'''

weather_json = '''{
    "current_temp": "22°C",
    "forecast": "Partly Cloudy",
    "phrase_line_1": "Don't forget your",
    "phrase_line_2": "Have a great day!"
}'''


# Parse JSON
def get_buses():
    return json.loads(buses_json)

def get_weather():
    return json.loads(weather_json)

# Image settings
WIDTH, HEIGHT = 800, 480
LEFT_MARGIN = 10
RIGHT_MARGIN = 10
BUS_RECT_W = 115
BUS_RECT_H = 60
BUS_SPACING = 20
TOP_MARGIN = 10

# Fonts (adjust path as needed)
try:
    FONT_LARGE = ImageFont.truetype("NotoSans.ttf", 42)
    FONT_MEDIUM = ImageFont.truetype("NotoSans.ttf", 34)
    FONT_SMALL = ImageFont.truetype("NotoSans.ttf", 30)
except:
    FONT_LARGE = FONT_MEDIUM = FONT_SMALL = ImageFont.load_default()

def draw_buses(draw, buses):
    y = TOP_MARGIN
    for bus in buses:
        # Full row for each bus
        row_left = LEFT_MARGIN
        row_right = WIDTH - RIGHT_MARGIN
        row_top = y
        row_bottom = y + BUS_RECT_H + 20
        # Draw bus number in black rectangle at left
        draw.rectangle([
            (row_left, row_top),
            (row_left + BUS_RECT_W, row_bottom)
        ], fill="black")
        bus_num = str(bus["number"])
        bbox_num = FONT_LARGE.getbbox(bus_num)
        w_num, h_num = bbox_num[2] - bbox_num[0], bbox_num[3] - bbox_num[1]
        num_x = row_left + (BUS_RECT_W - w_num) // 2
        num_y = row_top + (BUS_RECT_H - h_num) // 2
        draw.text((num_x, num_y), bus_num, fill="white", font=FONT_LARGE)

        # Destination next to number
        dest_x = row_left + BUS_RECT_W + 15
        bbox_dest = FONT_MEDIUM.getbbox(bus["destination"])
        w_dest = bbox_dest[2] - bbox_dest[0]
        h_dest = bbox_dest[3] - bbox_dest[1]
        dest_y = row_top + (BUS_RECT_H - h_dest) // 2
        draw.text((dest_x, dest_y), bus["destination"], fill="black", font=FONT_MEDIUM)

        # Time/minutes at far right of row
        if "minutes" in bus:
            time_str = f"{bus['minutes']} min"
        else:
            time_str = bus["time"]
        bbox_time = FONT_SMALL.getbbox(time_str)
        w_time = bbox_time[2] - bbox_time[0]
        h_time = bbox_time[3] - bbox_time[1]
        time_x = row_right - w_time
        time_y = row_top + (BUS_RECT_H - h_time) // 2
        draw.text((time_x, time_y), time_str, fill="black", font=FONT_SMALL)

        y += BUS_RECT_H + BUS_SPACING + 15

def draw_weather(draw, weather):
    # Draw a horizontal line below the buses
    y = TOP_MARGIN + 3 * (BUS_RECT_H + BUS_SPACING) + 45  # 3 buses, adjust if dynamic
    line_y = y
    draw.line([(LEFT_MARGIN, line_y), (WIDTH - RIGHT_MARGIN, line_y)], fill="black", width=2)
    y += 20

    # Left column: temp and forecast
    left_x = LEFT_MARGIN
    right_x = WIDTH // 2 + 10
    # Temp (large)
    draw.text((left_x, y), f"{weather['current_temp']}", fill="black", font=FONT_LARGE)
    y_temp = y + 50
    # Forecast (medium)
    draw.text((left_x, y_temp), f"{weather['forecast']}", fill="black", font=FONT_MEDIUM)

    # Right column: phrase
    phrase_x = right_x
    phrase_y = y
    draw.text((phrase_x, phrase_y), weather['phrase_line_1'], fill="black", font=FONT_MEDIUM)
    draw.text((phrase_x, phrase_y + 45), weather['phrase_line_2'], fill="black", font=FONT_MEDIUM)

def main():
    buses = get_buses()
    weather = get_weather()
    image = Image.new("1", (WIDTH, HEIGHT), 1)  # 1-bit image, white background
    draw = ImageDraw.Draw(image)
    # Draw left column (buses)
    draw_buses(draw, buses)
    # Draw right column (weather)
    draw_weather(draw, weather)
    # Save image
    image.save("dump.bmp")
    print("Bitmap image saved as dump.bmp")

if __name__ == "__main__":
    main()
    epd = epd4in26.EPD()
    epd.init_Fast()
    Himage = Image.open('dump.bmp')
    epd.display_Fast(epd.getbuffer(Himage))
