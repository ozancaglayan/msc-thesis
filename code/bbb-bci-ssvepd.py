import os
import sys
import time
import signal

import Adafruit_BBIO.GPIO as GPIO

PID_FILE = "/var/run/bbb-bci-ssvepd.pid"

# LED informations
LEDS = [["P8_9",  0, time.time(), 0, 0],
		["P8_10", 0, time.time(), 0, 0],
		]
PIN, VALUE, TIMER, PERIOD, HZ = range(5)

ENABLED = 0

def sigterm_handler(signum, stack):
	cleanup()
	sys.exit(0)

def cleanup():
	try:
		os.unlink(PID_FILE)
	except:
		pass
	for led in LEDS:
		GPIO.output(led[PIN], 0)
	GPIO.cleanup()

def sigusr1_handler(signum, stack):
	global ENABLED
	ENABLED ^= 1
	for led in LEDS:
		led[VALUE] = 0
		GPIO.output(led[PIN], led[VALUE])

	# If stimulation is turned off, block until another SIGUSR1
	if not ENABLED:
		signal.pause()

def write_pid_file():
	if os.path.exists(PID_FILE):
		return False
	with open(PID_FILE, "w") as fp:
		fp.write("%s" % os.getpid())
	return True

def main(freqs):
	# Setup pins
	for led in LEDS:
		GPIO.setup(led[PIN], GPIO.OUT)
		GPIO.output(led[PIN], led[VALUE])
		led[HZ] = int(freqs.pop(0))
		led[PERIOD] = 1 / (led[HZ] * 2.0)

	# Register signal handlers
	signal.signal(signal.SIGUSR1, sigusr1_handler)
	signal.signal(signal.SIGTERM, sigterm_handler)

	if not ENABLED:
		signal.pause()

	try:
		while 1:
			for led in LEDS:
				if (time.time() - led[TIMER]) >= led[PERIOD]:
					# Toggle led
					GPIO.output(led[PIN], led[VALUE] ^ 1)
					led[TIMER] = time.time()
					led[VALUE] ^= 1
	except KeyboardInterrupt, ke:
		return 2
	finally:
		cleanup()
		return 0

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "Usage: %s [--start] <freq1> <freq2> ... <freqN>" % sys.argv[0]
		sys.exit(1)

	# Start stimulation immediately
	if sys.argv[1] == "--start":
		ENABLED = 1
		sys.argv.remove("--start")

	sys.exit(main(sys.argv[1:]))
