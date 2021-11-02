# Raspberry Pi powered health tracking system

## How it works?

This project implements a home health tracking system. It measures the **heart rate**, **oxygen saturation** as well as the **temperature** and **humidity** of the environment.

A measurement is triggered by a push button. To ensure the highest accuracy possible (to the extent the hardware allows), the measurement takes 30 seconds - 15 seconds for heart rate, another 15 seconds for oxygen saturation. The countdown and the results are shown on a small OLED display (0.96" 128x64).

If the heart rate or oxygen saturation drop below or exceeds a critical threshold, a red LED blinks rapidly and an SMS is sent to a designated mobile number.

The health tracking part is supplemented by an environment monitor that periodically logs the current temperature and humidity.

Every measurement is logged in a database. The communication is facilitated by an API runnning in the background.


## Components used

- Raspberry Pi 3 Model B+
- MAX30102 Pulse Oximeter and Heart-Rate Sensor
- SHT31 Temperature and Humidity Sensor
- OLED 0.96" display 128x64
- Push button
- LED
- Resistors & Jumper Wires


## Diagram

![Fritzing diagram of the health tracking system](/images/fritzing.png)


## Installation and Setup

1. Clone this repositrory
2. Install dependencies with `pip install -r requirements.txt`
> Note the `requirements.txt` file is bloated due to extended experimentation during development.
> I will address this issue later on.

### API
1. Supplement your Twilio credentials in `api/twilio.env`
2. Run `source api/twilio.env`
3. Run `uvicorn api:app --reload`
  - this will give you a server running at `http://127.0.0.1:8000`

### Quickstart
- Run `python hr_spo2.py`
- Run `temp_sense.py` periodically
	1. Decide how often you want to run it (you can visit [crontab.guru](https://crontab.guru/) for help)
	2. `crontab -e` to edit crontab (for Linux)
	3. `{cron schedule expression} {python executable} {script}` (e.g. `* * * * * /home/pi/miniconda3/envs/py36/bin/python /home/pi/rpiot-health/temp_sense.py`)


## API

It uses the [FastAPI](https://fastapi.tiangolo.com/) library. A nice and handy feature is the documentation provided out of the box. The documentation is provided in two versions - Swagger and Redoc.

Use `http://localhost:8000/docs` for Swagger or `http://localhost:8000/redoc` for Redoc.

![Swagger documentation of the API](/images/docs.png)


## TODOS

- [ ] Use SQLAlchemy (API)
- [ ] Pagination (API)
- [ ] Write some tests
- [ ] Dockerize
- [ ] Use a config file for various configurable bits and pieces (e.g. mobile phone)
- [ ] Split up the `hr_spo2.py` script and move parts to the API
- [ ] Use a cloud provider for DB and API (Raspberry Pi as an interface to connect sensors to only)
- [ ] Use [Poetry](https://python-poetry.org/) for package and dependency management

## Limitations

For the purposes of this demonstration it is more than enough, however:
- First and foremost, some software design decisions (mostly due to time constraint when putting this project together).
- SQLite3 is generally slow.
- Only basic `uvicorn` has been installed, for some reason my Raspberry Pi wouldn't install the extra dependency `uvloop`. As pointed out in the [official docs](https://fastapi.tiangolo.com/deployment/manually/?h=uvicorn#install-the-server-program), `uvloop` is the high-performance replacement for `asyncio` which provides the increased concurrency performance.
- Last but not least, limited hardware of the Raspberry Pi.
