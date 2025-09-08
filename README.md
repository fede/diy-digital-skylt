# e-Paper Home Display

This project is a personal script to power a small e-ink display at home. It was built for fun as a weekend project, and is not intended to be a polished product—just a useful and hackable tool!

![Working digital sign](https://media.printables.com/media/prints/9bedc2fa-6c23-45ad-b755-586d454dae8b/images/10631876_3005836f-e381-4b29-b481-4a89298bab2e_e20a0b3a-d51b-42e3-8879-35abce522058/thumbs/inside/1920x1440/png/screenshot-2025-09-08-at-110744.webp)

## What does it do?

- **Bus Departures:** Shows the next buses leaving from my local bus stop (using Sweden's Trafiklab API).
- **Weather:** Displays the current weather and forecast (using Open-Meteo), so I don't forget an umbrella or jacket.
- **Calendar:** Shows the next event from my Apple Calendar (via iCloud integration).

All of this is shown on a 4.26-inch e-paper (e-ink) display, driven by a Raspberry Pi Zero W v1.

## Hardware

- Raspberry Pi Zero W v1
- 4.26" e-paper display (Waveshare)
- 3D-printed case ([Printables model](https://www.printables.com/model/1408332-digital-skylt))
- Some soldering and assembly required!
- Two M3 screws for assembling

## Software

- Python 3
- [Open-Meteo](https://open-meteo.com/) for weather data
- [Trafiklab](https://www.trafiklab.se/) for Swedish public transport
- iCloud for Apple Calendar events
- Pillow for image drawing
- Requests for HTTP API calls

The code is designed to be easily customizable—swap out the APIs or add your own data sources as you like.

## Usage

- The `main.py` script is the one you should schedule (e.g., with `cron`) on your Raspberry Pi to refresh the e-ink display. Running it every minute is a good idea:
  ```
  * * * * * /usr/bin/python3 /path/to/main.py
  ```
- The API server can be run either on the Raspberry Pi itself or on another server. Just make sure to set the correct API URL in your `.env` file. You can also set an API key for security, especially if the server is exposed to the internet.

## Disclaimer

This code is definitely not perfect! It was written quickly as a fun Saturday project, from designing and printing the 3D case to soldering, programming, and assembling the whole thing. If you want to improve it, go ahead!

## License

MIT (see LICENSE file)
