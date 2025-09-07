#!/usr/bin/env python3

import sys
import os
import json
import requests

from dotenv import load_dotenv

load_dotenv()

libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd4in26

API_URL = os.getenv("API_URL", "http://localhost:3000/display")
API_KEY = os.getenv("API_KEY", "your_auth_key_here")

DUMP_BMP_PATH = "/tmp/dump.bmp"

def fetch_api_response():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.get(API_URL, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API fetch error: {e}")
        return None

def get_buses(api_response):
    return api_response.get("buses", []) if api_response else []

def get_weather(api_response):
    return api_response.get("weather", {}) if api_response else {}

def get_calendar(api_response):
    return api_response.get("calendar", {}) if api_response else {}

WIDTH, HEIGHT = 800, 480
LEFT_MARGIN = 20
RIGHT_MARGIN = 20

BUS_RECT_W = 115
BUS_RECT_H = 50
BUS_SPACING = 25

TOP_MARGIN = 20

Y_OFFSET_BOTTOM_CONTENT = 325

ICON_MOON = "\uEF44"
ICON_CALENDAR = "\uEBCC"
ICON_RAINY = "\uF176"
ICON_TWILIGHT = "\uE1C6"
ICON_SUN = "\uE81A"

try:
    FONT_LARGE = ImageFont.truetype(os.path.join(libdir, "fonts/NotoSans-Regular.ttf"), 42)
    FONT_MEDIUM = ImageFont.truetype(os.path.join(libdir, "fonts/NotoSans-Regular.ttf"), 34)
    FONT_SMALL = ImageFont.truetype(os.path.join(libdir, "fonts/NotoSans-Regular.ttf"), 30)
    FONT_BOLD_LARGE = ImageFont.truetype(os.path.join(libdir, "fonts/NotoSans-Bold.ttf"), 42)
    FONT_BOLD_MEDIUM = ImageFont.truetype(os.path.join(libdir, "fonts/NotoSans-Bold.ttf"), 34)
    FONT_BOLD_SMALL = ImageFont.truetype(os.path.join(libdir, "fonts/NotoSans-Bold.ttf"), 30)
    ICON_LARGE = ImageFont.truetype(os.path.join(libdir, "fonts/MaterialSymbolsOutlined.ttf"), 42)
    ICON_MEDIUM = ImageFont.truetype(os.path.join(libdir, "fonts/MaterialSymbolsOutlined.ttf"), 34)
    ICON_SMALL = ImageFont.truetype(os.path.join(libdir, "fonts/MaterialSymbolsOutlined.ttf"), 30)
    FONT_EMOJI_LARGE = ImageFont.truetype(os.path.join(libdir, "fonts/NotoEmoji-VariableFont_wght.ttf"), 42)
    FONT_EMOJI_MEDIUM = ImageFont.truetype(os.path.join(libdir, "fonts/NotoEmoji-VariableFont_wght.ttf"), 34)
    FONT_EMOJI_SMALL = ImageFont.truetype(os.path.join(libdir, "fonts/NotoEmoji-VariableFont_wght.ttf"), 30)
except:
    FONT_LARGE = FONT_MEDIUM = FONT_SMALL = FONT_BOLD_LARGE = FONT_BOLD_MEDIUM = FONT_BOLD_SMALL = ICON_LARGE = ICON_MEDIUM = ICON_SMALL = ImageFont.load_default()

def draw_buses(draw, buses):
    y = TOP_MARGIN
    for bus in buses[:3]:
        row_left = LEFT_MARGIN
        row_right = WIDTH - RIGHT_MARGIN
        row_top = y
        row_bottom = y + BUS_RECT_H + 20
        
        draw.rectangle([
            (row_left, row_top),
            (row_left + BUS_RECT_W, row_bottom)
        ], fill="black")
        bus_num = str(bus["number"])
        bbox_num = FONT_BOLD_LARGE.getbbox(bus_num)
        w_num, h_num = bbox_num[2] - bbox_num[0], bbox_num[3] - bbox_num[1]
        num_x = row_left + (BUS_RECT_W - w_num) // 2
        num_y = row_top + (BUS_RECT_H - h_num) // 2
        draw.text((num_x, num_y), bus_num, fill="white", font=FONT_BOLD_LARGE)

        dest_x = row_left + BUS_RECT_W + 15
        bbox_dest = FONT_MEDIUM.getbbox(bus["destination"])
        h_dest = bbox_dest[3] - bbox_dest[1]
        dest_y = row_top + (BUS_RECT_H - h_dest) // 2
        draw.text((dest_x, dest_y), bus["destination"], fill="black", font=FONT_MEDIUM)

        if "minutes" in bus:
            time_str = f"{bus['minutes']}"
        else:
            time_str = bus["time"]
        bbox_time = FONT_BOLD_LARGE.getbbox(time_str)
        w_time = bbox_time[2] - bbox_time[0]
        h_time = bbox_time[3] - bbox_time[1]
        time_x = row_right - w_time
        time_y = row_top + (BUS_RECT_H - h_time) // 2
        draw.text((time_x, time_y), time_str, fill="black", font=FONT_BOLD_LARGE)

        y += BUS_RECT_H + BUS_SPACING + 15

def draw_separator(draw):
    line_y = Y_OFFSET_BOTTOM_CONTENT-20
    draw.line([(LEFT_MARGIN, line_y), (WIDTH - RIGHT_MARGIN, line_y)], fill="black", width=2)

def draw_weather(draw, weather):
    temp_text = f"{weather['current_temp']}"
    wind_text = f"{weather.get('wind_condition', '')}"
    
    draw.text((LEFT_MARGIN, Y_OFFSET_BOTTOM_CONTENT-3), temp_text, fill="black", font=FONT_BOLD_LARGE)
    
    if wind_text:
        bbox_temp = FONT_LARGE.getbbox(temp_text)
        w_temp = bbox_temp[2] - bbox_temp[0]
        wind_x = LEFT_MARGIN + w_temp + 15
        wind_y = Y_OFFSET_BOTTOM_CONTENT + 8 
        draw.text((wind_x, wind_y), wind_text, fill="black", font=FONT_SMALL)
    y_temp = Y_OFFSET_BOTTOM_CONTENT + 50
    
    low_temp_val = weather.get('later_temp', '-')
    later_temp_time = weather.get('later_temp_time', '-')

    if later_temp_time == "noon":
        bbox_icon = ICON_MEDIUM.getbbox(ICON_SUN)
    elif later_temp_time == "afternoon":
        bbox_icon = ICON_MEDIUM.getbbox(ICON_TWILIGHT)
    else:
        bbox_icon = ICON_MEDIUM.getbbox(ICON_MOON)
    h_icon = bbox_icon[3] - bbox_icon[1]
    bbox_temp = FONT_MEDIUM.getbbox(low_temp_val)
    h_temp = bbox_temp[3] - bbox_temp[1]
    
    icon_y = y_temp + (h_temp - h_icon) + 20 // 2
    draw.text((LEFT_MARGIN, icon_y), ICON_MOON, fill="black", font=ICON_MEDIUM)
    w_icon = bbox_icon[2] - bbox_icon[0]
    temp_x = LEFT_MARGIN + w_icon + 10
    draw.text((temp_x, y_temp), low_temp_val, fill="black", font=FONT_MEDIUM)
    
    precip_text = weather.get('precipitation', '')
    if precip_text:
        y_precip = y_temp + 40
        draw.text((LEFT_MARGIN, y_precip + 7), ICON_RAINY, fill="black", font=ICON_MEDIUM)
        bbox_rain = ICON_MEDIUM.getbbox(ICON_RAINY)
        w_rain = bbox_rain[2] - bbox_rain[0]
        precip_x = LEFT_MARGIN + w_rain + 10
        draw.text((precip_x, y_precip + 4), f"{precip_text}", fill="black", font=FONT_SMALL)

def is_emoji(char):
    codepoint = ord(char)
    return (
        0x1F600 <= codepoint <= 0x1F64F or  # emoticons
        0x1F300 <= codepoint <= 0x1F5FF or  # symbols & pictographs
        0x1F680 <= codepoint <= 0x1F6FF or  # transport & map
        0x1F700 <= codepoint <= 0x1F77F or  # alchemical
        0x1F780 <= codepoint <= 0x1F7FF or  # Geometric Shapes Extended
        0x1F800 <= codepoint <= 0x1F8FF or  # Supplemental Arrows-C
        0x1F900 <= codepoint <= 0x1F9FF or  # Supplemental Symbols and Pictographs
        0x1FA00 <= codepoint <= 0x1FA6F or  # Chess Symbols
        0x1FA70 <= codepoint <= 0x1FAFF or  # Symbols and Pictographs Extended-A
        0x2600 <= codepoint <= 0x26FF or    # Misc symbols
        0x2700 <= codepoint <= 0x27BF or    # Dingbats
        0xFE00 <= codepoint <= 0xFE0F or    # Variation Selectors
        0x1F1E6 <= codepoint <= 0x1F1FF     # Flags
    )

def draw_mixed_text(draw, pos, text, font, emoji_font, fill="black"):
    x, y = pos
    buffer = ""
    i = 0
    while i < len(text):
        char = text[i]
        if is_emoji(char):
            # Draw buffer with regular font
            if buffer:
                draw.text((x, y), buffer, fill=fill, font=font)
                w = font.getbbox(buffer)[2] - font.getbbox(buffer)[0]
                x += w
                buffer = ""
            # Draw emoji
            draw.text((x, y), char, fill=fill, font=emoji_font)
            w = emoji_font.getbbox(char)[2] - emoji_font.getbbox(char)[0]
            x += w
        else:
            buffer += char
        i += 1
    if buffer:
        draw.text((x, y), buffer, fill=fill, font=font)

def draw_calendar(draw, calendar):
    right_x = WIDTH // 2 + 10
    event_title = calendar.get('event_date', '')
    if event_title:
        bbox_icon = ICON_MEDIUM.getbbox(ICON_CALENDAR)
        h_icon = bbox_icon[3] - bbox_icon[1]
        bbox_title = FONT_MEDIUM.getbbox(event_title.upper())
        h_title = bbox_title[3] - bbox_title[1]
        icon_y = Y_OFFSET_BOTTOM_CONTENT + (h_title - h_icon) + 20 // 2
        draw.text((right_x, icon_y), ICON_CALENDAR, fill="black", font=ICON_MEDIUM)
        w_icon = bbox_icon[2] - bbox_icon[0]
        title_x = right_x + w_icon + 10
        draw.text((title_x, Y_OFFSET_BOTTOM_CONTENT), event_title.upper(), fill="black", font=FONT_BOLD_MEDIUM)
    event_desc_1 = calendar.get('event_desc_1', '')
    event_desc_2 = calendar.get('event_desc_2', '')
    if event_desc_1:
        draw_mixed_text(draw, (right_x, Y_OFFSET_BOTTOM_CONTENT+50), event_desc_1, FONT_MEDIUM, FONT_EMOJI_MEDIUM, fill="black")
    if event_desc_2:
        draw_mixed_text(draw, (right_x, Y_OFFSET_BOTTOM_CONTENT+90), event_desc_2, FONT_MEDIUM, FONT_EMOJI_MEDIUM, fill="black")

def main():
    api_response = fetch_api_response()
    buses = get_buses(api_response)
    weather = get_weather(api_response)
    calendar = get_calendar(api_response)
    image = Image.new("1", (WIDTH, HEIGHT), 1)
    draw = ImageDraw.Draw(image)
    draw_buses(draw, buses)
    draw_separator(draw)
    draw_weather(draw, weather)
    draw_calendar(draw, calendar)
    image.save(DUMP_BMP_PATH)

if __name__ == "__main__":
    main()
    epd = epd4in26.EPD()
    epd.init_Fast()
    Himage = Image.open(DUMP_BMP_PATH)
    epd.display_Fast(epd.getbuffer(Himage))
    epd.sleep()
