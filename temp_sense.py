# Code adapted from a blog post by SHEDBOY71
# (http://www.pibits.net/code/raspberry-pi-sht31-sensor-example.php)

import requests
import smbus
import time

API = 'http://127.0.0.1:8000'
 
bus = smbus.SMBus(1)
bus.write_i2c_block_data(0x44, 0x2C, [0x06])
 
time.sleep(0.5)
 
data = bus.read_i2c_block_data(0x44, 0x00, 6)
 
temp = data[0] * 256 + data[1]
cTemp = -45 + (175 * temp / 65535.0)
fTemp = -49 + (315 * temp / 65535.0)
humidity = 100 * (data[3] * 256 + data[4]) / 65535.0

body = {
		'temperature': cTemp,
		'humidity': humidity
	}
requests.post(f'{API}/env', json=body)