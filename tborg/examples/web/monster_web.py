#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Creates a web-page interface for the MonsterBorg.
#
# <IP>:9000/
# or
# <IP>:9000/hold
#
__docformat__ = "restructuredtext en"

import time
import datetime
import mimetypes
import os
import sys
import threading
import cv2
import logging

from socketserver import ThreadingMixIn, TCPServer, BaseRequestHandler
from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.append(BASE_DIR)

from tborg import create_working_dir, ConfigLogger, ThunderBorg
from tborg.utils.daemon import Daemon


def is_raspberry_pi():
    # Method 1: Check /proc/cpuinfo
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Hardware') or line.startswith('Model'):
                    return 'Raspberry Pi' in line
    except FileNotFoundError:
        pass

    # Method 2: Check device tree (fallback)
    try:
        with open('/sys/firmware/devicetree/base/model', 'r') as f:
            return 'Raspberry Pi' in f.read()
    except (FileNotFoundError, PermissionError):
        pass

    return False


if is_raspberry_pi():
    from picamera2 import Picamera2

create_working_dir()

from tborg import LOG_PATH, RUN_PATH, MEDIA_PATH


class Watchdog(threading.Thread):
    """
    Timeout thread
    """
    def __init__(self, tb, log_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tb = tb
        self._log = logging.getLogger(log_name)
        self.event = threading.Event()
        self.terminated = False
        self.start()

    def run(self):
        timed_out = True

        # This method runs in a separate thread
        while not self.terminated:
            # Wait for a network event to be flagged for up to one second
            if timed_out:
                if self.event.wait(1):
                    # Connection
                    self._log.info("Reconnected...")
                    self.tb.set_led_battery_state(True)
                    timed_out = False
                    self.event.clear()
            else:
                if self.event.wait(1):
                    self.event.clear()
                else:
                    # Timed out
                    self._log.warning("Timed out...")
                    self.tb.set_led_battery_state(False)
                    self.tb.set_both_leds(0, 0, 1)
                    timed_out = True
                    self.tb.halt_motors()


class StreamProcessor(threading.Thread):
    """
    Image stream processing thread
    """
    def __init__(self, global_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.global_data = global_data
        self.event = threading.Event()
        self.terminated = False
        self.start()
        self.begin = 0

    def run(self):
        while not self.terminated:
            if self.event.wait(1):
                try:
                    frame = self.frame

                    if self.global_data['flipped_camera']:
                        frame = cv2.flip(frame, -1)

                    _, jpeg = cv2.imencode('.jpg', frame,
                                           [cv2.IMWRITE_JPEG_QUALITY,
                                            self.global_data['jpeg_quality']])

                    with self.global_data['lock_frame']:
                        self.global_data['last_frame'] = jpeg.tobytes()

                finally:
                    self.event.clear()


class ImageCapture(threading.Thread):
    """
    Image capture thread
    """
    def __init__(self, camera, processor, running, log_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera = camera
        self.processor = processor
        self.running = running
        self._log = logging.getLogger(log_name)
        self.start()

    def run(self):
        self._log.info("Start the stream using the video port.")

        while self.running:
            # Wait until processor is ready
            if self.processor.event.is_set():
                time.sleep(0.001)
                continue

            request = self.camera.capture_request()
            self.processor.frame = cv2.cvtColor(request.make_array("main"),
                                                cv2.COLOR_RGB2BGR)
            request.release()
            self.processor.event.set()

        self._log.info("Terminating camera processing...")
        self.processor.terminated = True
        self.processor.join()
        self._log.info("Processing terminated.")


class ThreadingTCPServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class WebServer(BaseRequestHandler):
    """
    Class used to implement the web server
    """
    GLOBAL_DATA = None

    def handle(self):
        self.tb = self.GLOBAL_DATA['tb']
        log_name = self.GLOBAL_DATA['log_name']
        lock_frame = self.GLOBAL_DATA['lock_frame']
        watchdog = self.GLOBAL_DATA['watchdog']
        max_power = self.GLOBAL_DATA['max_power']
        req_data = self.parse_request(self.request)
        self._log = logging.getLogger(log_name)
        # Get the URL requested
        self.temp_path = os.path.join(BASE_DIR, 'tborg', 'examples', 'web',
                                      'templates')
        url_path = ''
        line = req_data.get('GET')
        self._log.debug("line: %s", line)

        if line:
            parts = line.split(' ')
            url_path = parts[0]

        # Serve static files from the templates directory
        if url_path.startswith('/stream.mjpg'):
            self._serve_mjpeg_stream()
        elif url_path.endswith((".js", ".css", ".png", ".ico", ".jpg")):
            self._log.info("media: %s", url_path)
            self._serve_static(url_path)
        elif url_path.startswith('/halt'):
            # Turn the drives off
            self._log.info("halt: %s", url_path)
            self._render_template('set.html', title="Halt Motors",
                                  percent_left=0, percent_right=0)

            if self.tb:
                self.tb.halt_motors()
                watchdog.event.set()
        elif url_path.startswith('/set'):
            # Motor power setting: /set/left/right
            self._log.info("set: %s", url_path)
            parts = url_path.split('/')

            # Get the power levels
            if len(parts) >= 4:
                try:
                    drive_left = float(parts[2])
                    drive_right = float(parts[3])
                except Exception:
                    # Bad values
                    drive_right = 0.0
                    drive_left = 0.0
            else:
                # Bad request
                drive_right = 0.0
                drive_left = 0.0

            # Ensure settings are within limits
            if drive_right < -1:
                drive_right = -1
            elif drive_right > 1:
                drive_right = 1

            if drive_left < -1:
                drive_left = -1
            elif drive_left > 1:
                drive_left = 1

            # Report the current settings
            percent_left = drive_left * 100.0
            percent_right = drive_right * 100.0
            self._render_template("set.html", title="Set Motor",
                                  percent_left=percent_left,
                                  percent_right=percent_right)
            # Set the outputs
            drive_left *= max_power
            drive_right *= max_power

            if self.tb:
                self.tb.set_motor_one(drive_right)
                self.tb.set_motor_two(drive_left)
                watchdog.event.set()
        elif url_path.startswith('/photo'):
            # Save camera photo
            self._log.info("photo: %s", url_path)
            lock_frame.acquire()
            capture_frame = self.GLOBAL_DATA['last_frame']
            lock_frame.release()

            if capture_frame is not None:
                dt = datetime.datetime.now(datetime.UTC)
                filename = f"photo-{dt.strftime('%Y%m%d-%H%M%S-%f')}.jpg"
                photo_name = os.path.join(MEDIA_PATH, filename)

                try:
                    with open(photo_name, 'wb') as f:
                        f.write(capture_frame)

                    msg = f"Photo saved to {photo_name}"
                except Exception:
                    msg = 'Failed to take photo!'
            else:
                msg = 'Failed to take photo!'

            self._render_template("photo.html", title="Photo", msg=msg)
        elif url_path == '/' or url_path == "/index.html":
            # Main page, click buttons to move and to stop
            self._log.info("/: %s", url_path)
            self._render_template("index.html", title="Main Page")
        elif url_path == '/hold':
            # Alternate page, hold buttons to move (does not work with
            # all devices)
            self._log.info("hold: %s", url_path)
            self._render_template("hold.html", title="Hold")
        elif url_path == '/stream':
            # Streaming frame, set a delayed refresh
            self._log.info("stream: %s", url_path)
            self._render_template("stream.html", title="Robot Camera")
        else:
            self._log.info("Unknown: %s", url_path)
            self._send(404, 'Not Found', 'text/html', f'Path : "{url_path}"')

    def parse_request(self, request):
        """
        Create a file-like object from the socket where 'r' mode reads text
        (bytes are decoded using default encoding, usually utf-8).
        You can specify encoding explicitly if needed: encoding='utf-8'
        """
        data = {}

        with request.makefile('r') as f:
            for line in f:
                # line includes the \r\n, so strip it
                clean_line = line.strip()

                if not clean_line:
                    break  # Stop at empty line (common in HTTP)
                else:
                    idx = clean_line.index(' ')
                    data[clean_line[:idx]] = clean_line[idx+1:]

        return data

    def _render_template(self, name, **context):
        env = Environment(loader=FileSystemLoader(self.temp_path))
        tmpl = env.get_template(name)
        body = tmpl.render(**context).encode()
        self._send(200, 'OK', "text/html", body)

    def _serve_static(self, filename):
        filename = filename.lstrip("/")
        filepath = os.path.join(self.temp_path, filename)

        if os.path.isfile(filepath):
            mime, _ = mimetypes.guess_type(filepath)
            mime = mime or "application/octet-stream"
            self._log.info("filename: %s, mine: %s", filename, mime)

            with open(filepath, "rb") as f:
                body = f.read()

            self._send(200, 'OK', mime, body)
        else:
            self._send(404, 'Not Found', 'text/plain', b"Not Found")

    def _serve_mjpeg_stream(self):
        self.request.sendall(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
            b"Cache-Control: no-cache\r\n"
            b"Connection: close\r\n"
            b"\r\n")

        try:
            while True:
                with self.GLOBAL_DATA['lock_frame']:
                    frame = self.GLOBAL_DATA['last_frame']

                if frame is not None:
                    self.request.sendall(
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: " +
                        str(len(frame)).encode() +
                        b"\r\n\r\n" +
                        frame +
                        b"\r\n")

                time.sleep(1 / self.GLOBAL_DATA['fps'])  # Frames Per Ssecond

        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send(self, status, reason, content_type, body: bytes):
        response = (
            f"HTTP/1.1 {status} {reason}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Connection: close\r\n"
            f"\r\n").encode() + body
        self.request.sendall(response)


class MonsterWeb(Daemon):
    _LOG_PATH = os.path.join(LOG_PATH, 'monster_web.log')
    _BASE_LOGGER_NAME = 'examples'
    _LOGGER_NAME = f'{_BASE_LOGGER_NAME}.monster_web'
    _TBORG_LOGGER_NAME = 'examples.tborg'
    _PIDFILE = os.path.join(RUN_PATH, 'monster_web.pid')
    IMAGE_WIDTH = 240
    """
    int: Width of the captured image in pixels
    """
    IMAGE_HEIGHT = 192
    """
    int: Height of the captured image in pixels
    """
    FRAME_RATE = 20
    """
    int: Number of images to capture per second
    """
    FLIPPED_CAMERA = True
    """
    bool: Swap between True and False if the camera image is rotated by 180.
    """
    JPEG_QUALITY = 80
    """
    int: JPEG quality level, smaller is faster, higher looks better (0 to 100)
    """
    # These were all global to the module.
    LAST_FRAME = None
    LOCK_FRAME = threading.Lock()
    MAX_POWER = 0

    def __init__(self, options, port=9000,
                 address=ThunderBorg.DEFAULT_I2C_ADDRESS,
                 log_level=logging.INFO, *args, **kwargs):
        super().__init__(self._PIDFILE, logger_name=self._LOGGER_NAME,
                         *args, **kwargs)
        self.port = port
        cl = ConfigLogger()
        cl.config(logger_name=self._BASE_LOGGER_NAME, file_path=self._LOG_PATH,
                  level=log_level)
        self._log = logging.getLogger(self._LOGGER_NAME)
        self._log.info("Starting MonsterWeb...")
        self._log.info("Set to level: %s", logging.getLevelName(log_level))
        self._borg = options.borg
        self.camera = None
        self.processor = None
        self.watchdog = None
        self.running = True
        self.tb = None

        if self._borg:
            self.tb = ThunderBorg(logger_name=self._TBORG_LOGGER_NAME,
                                  address=address, log_level=logging.INFO)
            voltage_in = float(options.voltage_in)
            self.tb.set_comms_failsafe(False)
            self.tb.set_led_battery_state(False)
            self.tb.set_both_leds(0, 0, 1)

            # Power settings
            self.tb.set_battery_limits(voltage_in)

            # Maximum motor voltage, we limit it to 95% to allow the RPi to get
            # uninterrupted power
            voltage_out = self.tb.get_battery_voltage() * 0.95

            # Setup the power limits
            if voltage_out > voltage_in:  # This may never happen.
                self.MAX_POWER = 1.0
            else:
                self.MAX_POWER = voltage_out / voltage_in

        self.global_data = {'tb': self.tb,
                            'log_name': self._LOGGER_NAME,
                            'fps': self.FRAME_RATE,
                            'flipped_camera': self.FLIPPED_CAMERA,
                            'jpeg_quality': self.JPEG_QUALITY,
                            'last_frame': self.LAST_FRAME,
                            'lock_frame': self.LOCK_FRAME,
                            'camera': self.camera,
                            'processor': self.processor,
                            'watchdog': self.watchdog,
                            'max_power': self.MAX_POWER,
                            }

    def run(self):
        try:
            self.create_image_buffer_frame()
        except Exception:
            self._log.error("monster_web.py failed to start.", exc_info=True)
            sys.exit(1)
        else:
            if self._borg:
                # Turn on failsafe.
                self._tb.set_comms_failsafe(True)

                if self._tb.get_comms_failsafe():
                    # Log and init
                    self.log_battery_monitoring()
                else:
                    self._log.error("The failsafe mode could not be "
                                    "turned on.")
                    self.running = False

                sys.exit(0)

    def create_image_buffer_frame(self):
        """
        Create the image buffer frame.
        """
        # Startup sequence
        if self._borg:
            self.camera = Picamera2()
            config = self.camera.create_video_configuration(
                main={"size": (self.IMAGE_WIDTH, self.IMAGE_HEIGHT),
                      "format": "BGR888"},
                controls={"FrameDurationLimits": (
                    int(1_000_000 / self.FRAME_RATE),
                    int(1_000_000 / self.FRAME_RATE))})
            self.camera.configure(config)
            self.camera.start()
            # Color adaption
            # 0 Auto
            # 1 Tungsten
            # 2 Fluorescent
            # 3 Indoor
            # 4 Daylight
            # 5 Cloudy
            self.camera.set_controls({"AwbMode": 0})

            self._log.info("Setup the stream processing thread")
            self.processor = StreamProcessor(self.global_data)
            self._log.info("Wait ...")
            time.sleep(2)
            capture_thread = ImageCapture(self.camera, self.processor,
                                          self.running, self._LOGGER_NAME)
            self._log.info("Setup the watchdog")
            self.watchdog = Watchdog(self.tb, self._LOGGER_NAME)

        # Run the web server until we are told to close
        try:
            WebServer.GLOBAL_DATA = self.global_data
            http_server = ThreadingTCPServer(("0.0.0.0", self.port), WebServer)
            http_server.allow_reuse_address = True
        except Exception as e:
            # Failed to open the port, report common issues
            self._log.info(f"\nFailed to open port {self.port}")
            self._log.info("Other problems include running another script "
                           "with the same port.")
            self._log.info("If the script was just working recently try "
                           "waiting a minute first.\n")
            # Flag the script to exit
            self.running = False
            raise e
        else:
            while self.running:
                http_server.handle_request()

            # Turn the motors off under all scenarios
            if self.options.borg:
                self.tb.halt_motors()
                self._log.info("Motors off")

            # Tell each thread to stop, and wait for them to end
            if http_server is not None:
                http_server.server_close()

            self.running = False
            capture_thread.join()
            self.processor.terminated = True
            self.watchdog.terminated = True
            self.processor.join()
            self.watchdog.join()
            self.CAMERA = None

            if self.options.borg:
                self.tb.set_led_battery_state(False)
                self.tb.set_both_leds(0, 0, 0)
                self.tb.halt_motors()

            self._log.info("Web-server terminated.")


if __name__ == "__main__":
    import argparse
    import traceback

    parser = argparse.ArgumentParser(
        description=("MonsterBorg control using a camera and web interface."))
    parser.add_argument(
        '-b', '--borg', action='store_false', default=True, dest='borg',
        help="The ThunderBorg code is not run.")
    parser.add_argument(
        '-d', '--debug', action='store_true', default=False, dest='debug',
        help="Run in debug mode (no thunderborg code is run).")
    parser.add_argument(
        '-v', '--voltage-in', type=float, default=12, dest='voltage_in',
        help=("The total voltage from the battery source, defaults to 12. "
              "If set to 0 (zero) the voltage is auto detected."))
    parser.add_argument(
        '-s', '--start', action='store_true', default=False, dest='start',
        help="Start the daemon.")
    parser.add_argument(
        '-r', '--restart', action='store_true', default=False, dest='restart',
        help="Restart the daemon.")
    parser.add_argument(
        '-S', '--stop', action='store_true', default=False, dest='stop',
        help="Stop the daemon.")
    options = parser.parse_args()
    arg_value = (options.start ^ options.restart ^ options.stop)

    if not arg_value and arg_value is not False:
        print("Can only set one of 'start', 'restart' or 'stop'.")
        sys.exit(-1)

    if options.start:
        arg = 'start'
    elif options.restart:
        arg = 'restart'
    elif options.stop:
        arg = 'stop'
    else:
        arg = 'start'

    ret = 0

    try:
        mw = MonsterWeb(options, log_level=logging.DEBUG)
    except Exception:
        tb = sys.exc_info()[2]
        traceback.print_tb(tb)
        print(f"{sys.exc_info()[0]}: {sys.exc_info()[1]}\n")
        ret = 1
    else:
        getattr(mw, arg)()

    sys.exit(ret)
