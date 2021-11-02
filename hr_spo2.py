# Ported version of the MaximIntegrated RD117_ARDUINO library used
# https://github.com/vrano714/max30102-tutorial-raspberrypi
# 
# Ported version of the SparkFun MAX3010x library used
# https://github.com/sparkfun/Qwiic_MAX3010x_Py

import time
import sys
import threading
import numpy as np
import hrcalc
import qwiic_max3010x
from max30102 import MAX30102
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
from abc import ABC, abstractmethod
import logging
from multiprocessing import Process, Value
import requests
from display import Display


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

MEASURE_SECONDS = 15
API = 'http://127.0.0.1:8000'
HR_THRESHOLD = {'min': 20, 'max': 180}
OXYGEN_THRESHOLD = 94

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

LED_PIN = 5
GPIO.setup(LED_PIN, GPIO.OUT)

display = Display()


class Monitor(ABC):

	def timer(self):
		display.countdown(15)

	@abstractmethod
	def start_sensor(self):
		pass

	@abstractmethod
	def stop_sensor(self):
		pass

	@abstractmethod
	def run_sensor(self):
		pass


class SPO2Monitor(Monitor):
	"""
	SpO2 monitor. It handles the measurement and calculation of 
	oxygen saturation.
	"""

	LOOP_TIME = 0.5

	def __init__(self, log=True):
		self.log = log
		self.result = Value('f', 0.0)

	def start_sensor(self, seconds=15):
		self.sensor = MAX30102()
		t_timer = Process(target=self.timer)
		t_sensor = Process(target=self.run_sensor, args=(seconds,))
		t_timer.start()
		t_sensor.start()
		t_timer.join()
		t_sensor.join()
		return self.result.value

	def stop_sensor(self):
		try:
			self.sensor.shutdown()
		except AttributeError:
			raise Exception('Sensor not running, start the sensor first!')
		
	def run_sensor(self, seconds):
		ir_data = []
		red_data = []
		spo2_global = []
		readings = []

		end_time = datetime.now() + timedelta(seconds=seconds)
		while datetime.now() < end_time:
			num_bytes = self.sensor.get_data_present()
			if num_bytes > 0:
                # grab all the data and stash it into arrays
				while num_bytes > 0:
					red, ir = self.sensor.read_fifo()
					num_bytes -= 1
					ir_data.append(ir)
					red_data.append(red)

				while len(ir_data) > 100:
					ir_data.pop(0)
					red_data.pop(0)

				if len(ir_data) == 100:
					_, _, spo2, valid_spo2 = hrcalc.calc_hr_and_spo2(ir_data, red_data)
					if valid_spo2:
						spo2_global.append(spo2)
						while len(spo2_global) > 4:
							spo2_global.pop(0)
						spo2 = np.mean(spo2_global)
						readings.append(spo2)
						if (np.mean(ir_data) < 50000 and np.mean(red_data) < 50000):
							spo2 = 0
							if self.log:
								logging.info('Finger not detected')
						if self.log:
							logging.info('SpO2: %d', spo2)

			time.sleep(self.LOOP_TIME)

		self.result.value = np.median(readings)


class HRMonitor(Monitor):
	"""
	Heart rate monitor. It handles the measurement and calculation of 
	heart rate in beats per minute.
	"""

	def __init__(self, log=True):
		self.log = log
		self.result = Value('f', 0.0)

	def millis(self):
		return int(round(time.time() * 1000))

	def start_sensor(self, seconds=15):
		self.sensor = qwiic_max3010x.QwiicMax3010x()
		if self.sensor.begin() == False:
			print("The Qwiic MAX3010x device isn't connected to the system. Please check your connection", \
				file=sys.stderr)
			return
		if self.sensor.setup() == False:
			print("Device setup failure. Please check your connection", \
				file=sys.stderr)
			return
		
		self.sensor.setPulseAmplitudeRed(0x0A) # Turn Red LED to low to indicate sensor is running
		self.sensor.setPulseAmplitudeGreen(0) # Turn off Green LED

		t_timer = Process(target=self.timer)
		t_sensor = Process(target=self.run_sensor, args=(seconds,))
		t_timer.start()
		t_sensor.start()
		t_timer.join()
		t_sensor.join()

		return self.result.value

	def stop_sensor(self):
		try:
			self.sensor.shutDown()
		except AttributeError:
			raise Exception('Sensor not running, start the sensor first!')

	def run_sensor(self, seconds):

		RATE_SIZE = 2
		rates = list(range(RATE_SIZE))
		rateSpot = 0
		lastBeat = 0
		beatsPerMinute = 0.00
		beatAvg = 0
		samplesTaken = 0
		startTime = self.millis()
		bpms = []

		end_time = datetime.now() + timedelta(seconds=seconds)
		while datetime.now() < end_time:
					
			irValue = self.sensor.getIR()

			samplesTaken += 1

			if self.sensor.checkForBeat(irValue) == True:
				delta = ( self.millis() - lastBeat )
				lastBeat = self.millis()
		
				beatsPerMinute = 60 / (delta / 1000.0)
				beatsPerMinute = round(beatsPerMinute,1)
		
				if beatsPerMinute < 255 and beatsPerMinute > 20:
					rateSpot += 1
					rateSpot %= RATE_SIZE
					rates[rateSpot] = beatsPerMinute

					# Take average of readings
					beatAvg = 0
					for x in range(0, RATE_SIZE):
						beatAvg += rates[x]
					beatAvg /= RATE_SIZE
					beatAvg = round(beatAvg)
					bpms.append(beatAvg)
			
			Hz = round(float(samplesTaken) / ( ( self.millis() - startTime ) / 1000.0 ) , 2)

			if (samplesTaken % 100 ) == 0:
				if self.log:
					logging.info('BPM = %d , AVG = %d', beatsPerMinute, beatAvg)

		self.result.value = np.median(bpms)

		return self.result


def blink_led():
	for i in range(6):
		GPIO.output(LED_PIN, True)
		time.sleep(0.1)
		GPIO.output(LED_PIN, False)
		time.sleep(0.1)


def callback(channel):

	metrics = {
		'hr': {
			'monitor': HRMonitor(log=False),
			'result': 0
		},
		'spo2': {
			'monitor': SPO2Monitor(log=False),
			'result': 0
		}
	}

	for _ , metric in enumerate(metrics):
		logging.info('Running %s', metric)
		display.show(metric)
		time.sleep(1)
		metrics[metric]['result'] = metrics[metric]['monitor'].start_sensor(seconds=MEASURE_SECONDS)
		metrics[metric]['monitor'].stop_sensor()

	hr, spo2 = metrics['hr']['result'], metrics['spo2']['result']
	txt = 'HR: {:.2f} bpm\nSpO2: {:.2f} %'.format(hr, spo2)
	display.show(txt, 'center', 12)
	body = {
		'heart_rate': hr,
		'oxygen_saturation': spo2
	}
	requests.post(f'{API}/health', json=body)

	if (hr < HR_THRESHOLD['min'] or hr > HR_THRESHOLD['max']) or (spo2 < OXYGEN_THRESHOLD):
		blink_led()
		logging.info('Sending SMS alert')
		requests.post(f'{API}/sms_alert', json=body)


if __name__ == '__main__':

	try:
		GPIO.add_event_detect(26,GPIO.RISING,callback=callback)
		message = input("Press enter to quit\n\n")
	except (KeyboardInterrupt, SystemExit) as err:
		print('Ending...')
		display.clear()
		GPIO.cleanup()
		sys.exit(0)
