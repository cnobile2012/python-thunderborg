#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Creates a web-page interface for the MonsterBorg.
#
__docformat__ = "restructuredtext en"

import time
import sys
import threading
import cv2
import datetime

from picamera2 import Picamera2
from socketserver import TCPServer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from tborg import (create_working_dir, ConfigLogger, ThunderBorg,
                   ThunderBorgException)

create_working_dir()

from tborg import LOG_PATH, RUN_PATH


class Watchdog(threading.Thread):
    """
    Timeout thread
    """
    def __init__(self, tb, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tb = tb
        self.event = threading.Event()
        self.terminated = False
        self.start()
        self.timestamp = time.time()

    def run(self):
        timed_out = True

        # This method runs in a separate thread
        while not self.terminated:
            # Wait for a network event to be flagged for up to one second
            if timed_out:
                if self.event.wait(1):
                    # Connection
                    print("Reconnected...")
                    self.tb.set_led_battery_state(True)
                    timed_out = False
                    self.event.clear()
            else:
                if self.event.wait(1):
                    self.event.clear()
                else:
                    # Timed out
                    print("Timed out...")
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
        self.flipped_camera = global_data['flipped_camera']
        self.jpeg_quality = global_data['jpeg_quality']
        self.last_frame = global_data['last_frame']
        self.lock_frame = global_data['lock_frame']
        self.camera = global_data['camera']

        self.stream = self.camera.capture_array()
        self.event = threading.Event()
        self.terminated = False
        self.start()
        self.begin = 0

    def run(self):
        # This method runs in a separate thread
        while not self.terminated:
            # Wait for an image to be written to the stream
            if self.event.wait(1):
                try:
                    # Read the image and save globally
                    self.stream.seek(0)

                    if self.flipped_camera:
                        # Flips X and Y
                        flipped_array = cv2.flip(self.stream.array, -1)
                        retval, this_frame = cv2.imencode(
                            '.jpg', flipped_array,
                            [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
                        del flipped_array
                    else:
                        retval, this_frame = cv2.imencode(
                            '.jpg', self.stream.array,
                            [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])

                    self.lock_frame.acquire()
                    self.last_frame = this_frame
                    self.lock_frame.release()
                finally:
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()


class ImageCapture(threading.Thread):
    """
    Image capture thread
    """
    def __init__(self, camera, processor, running, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera = camera  # Already configured and started.
        self.processor = processor
        self.running = running
        self.start()

    def run(self):
        print("Start the stream using the video port.")

        while self.running:
            # Wait until processor is ready
            if self.processor.event.is_set():
                time.sleep(0.001)
                continue

            request = self.camera.capture_request()
            self.processor.frame = request.make_array("main")
            request.release()
            self.processor.event.set()

        print("Terminating camera processing...")
        self.processor.terminated = True
        self.processor.join()
        print("Processing terminated.")


class WebServer(SocketServer.BaseRequestHandler):
    """
    Class used to implement the web server
    """
    GLOBAL_DATA = None

    def handle(self):
        # Get the HTTP request data
        lock_frame = self.GLOBAL_DATA['lock_frame']
        watchdog = self.GLOBAL_DATA['watchdog']
        max_power = self.GLOBAL_DATA['max_power']
        req_data = self.request.recv(1024).strip()
        req_data = req_data.split('\n')
        # Get the URL requested
        get_path = ''

        for line in req_data:
            if line.startswith('GET'):
                parts = line.split(' ')
                get_path = parts[1]
                break

        self.watchdog.event.set()

        if get_path.startswith('/cam.jpg'):
            # Camera snapshot
            lock_frame.acquire()
            send_frame = self.GLOBAL_DATA['last_frame']
            lock_frame.release()

            if send_frame is not None:
                self.send(send_frame.tostring())
        elif get_path.startswith('/off'):
            # Turn the drives off
            httpText = '<html><body><center>'
            httpText += 'Speeds: 0 %, 0 %'
            httpText += '</center></body></html>'
            self.send(httpText)
            self.tb.halt_motors()
        elif get_path.startswith('/set/'):
            # Motor power setting: /set/driveLeft/driveRight
            parts = get_path.split('/')

            # Get the power levels
            if len(parts) >= 4:
                try:
                    driveLeft = float(parts[2])
                    driveRight = float(parts[3])
                except Exception:
                    # Bad values
                    driveRight = 0.0
                    driveLeft = 0.0
            else:
                # Bad request
                driveRight = 0.0
                driveLeft = 0.0

            # Ensure settings are within limits
            if driveRight < -1:
                driveRight = -1
            elif driveRight > 1:
                driveRight = 1

            if driveLeft < -1:
                driveLeft = -1
            elif driveLeft > 1:
                driveLeft = 1

            # Report the current settings
            percentLeft = driveLeft * 100.0
            percentRight = driveRight * 100.0
            httpText = '<html><body><center>'
            httpText += f'Speeds: {percentLeft:.0f}%, {percentRight:.0f}%'
            httpText += '</center></body></html>'
            self.send(httpText)
            # Set the outputs
            driveLeft *= max_power
            driveRight *= max_power
            self.tb.set_motor_one(driveRight)
            self.tb.set_motor_two(driveLeft)
        elif get_path.startswith('/photo'):
            # Save camera photo
            lock_frame.acquire()
            captureFrame = self.GLOBAL_DATA['last_frame']
            lock_frame.release()
            httpText = '<html><body><center>'

            if captureFrame is not None:
                tz = datetime.UTC
                dt = datetime.datetime.now(tz)
                photo_directory = self.GLOBAL_DATA['photo_directory']
                photo_name = f"{photo_directory}/Photo-{dt}.jpg"

                try:
                    with open(photo_name, 'wb') as f:
                        f.write(captureFrame)

                    httpText += f"Photo saved to {photo_name}"
                except Exception:
                    httpText += 'Failed to take photo!'
            else:
                httpText += 'Failed to take photo!'

            httpText += '</center></body></html>'
            self.send(httpText)
        elif get_path == '/':
            # Main page, click buttons to move and to stop
            httpText = '<html>\n'
            httpText += '<head>\n'
            httpText += '<script language="JavaScript"><!--\n'
            httpText += 'function Drive(left, right) {\n'
            httpText += ' var iframe = document.getElementById("setDrive");\n'
            httpText += ' var slider = document.getElementById("speed");\n'
            httpText += ' left *= speed.value / 100.0;'
            httpText += ' right *= speed.value / 100.0;'
            httpText += ' iframe.src = "/set/" + left + "/" + right;\n'
            httpText += '}\n'
            httpText += 'function Off() {\n'
            httpText += ' var iframe = document.getElementById("setDrive");\n'
            httpText += ' iframe.src = "/off";\n'
            httpText += '}\n'
            httpText += 'function Photo() {\n'
            httpText += ' var iframe = document.getElementById("setDrive");\n'
            httpText += ' iframe.src = "/photo";\n'
            httpText += '}\n'
            httpText += '//--></script>\n'
            httpText += '</head>\n'
            httpText += '<body>\n'
            httpText += '<iframe src="/stream" width="100%" height="500" frameborder="0"></iframe>\n'
            httpText += '<iframe id="setDrive" src="/off" width="100%" height="50" frameborder="0"></iframe>\n'
            httpText += '<center>\n'
            httpText += '<button onclick="Drive(-1,1)" style="width:200px;height:100px;"><b>Spin Left</b></button>\n'
            httpText += '<button onclick="Drive(1,1)" style="width:200px;height:100px;"><b>Forward</b></button>\n'
            httpText += '<button onclick="Drive(1,-1)" style="width:200px;height:100px;"><b>Spin Right</b></button>\n'
            httpText += '<br /><br />\n'
            httpText += '<button onclick="Drive(0,1)" style="width:200px;height:100px;"><b>Turn Left</b></button>\n'
            httpText += '<button onclick="Drive(-1,-1)" style="width:200px;height:100px;"><b>Reverse</b></button>\n'
            httpText += '<button onclick="Drive(1,0)" style="width:200px;height:100px;"><b>Turn Right</b></button>\n'
            httpText += '<br /><br />\n'
            httpText += '<button onclick="Off()" style="width:200px;height:100px;"><b>Stop</b></button>\n'
            httpText += '<br /><br />\n'
            httpText += '<button onclick="Photo()" style="width:200px;height:100px;"><b>Save Photo</b></button>\n'
            httpText += '<br /><br />\n'
            httpText += '<input id="speed" type="range" min="0" max="100" value="100" style="width:600px" />\n'
            httpText += '</center>\n'
            httpText += '</body>\n'
            httpText += '</html>\n'
            self.send(httpText)
        elif get_path == '/hold':
            # Alternate page, hold buttons to move (does not work with all devices)
            httpText = '<html>\n'
            httpText += '<head>\n'
            httpText += '<script language="JavaScript"><!--\n'
            httpText += 'function Drive(left, right) {\n'
            httpText += ' var iframe = document.getElementById("setDrive");\n'
            httpText += ' var slider = document.getElementById("speed");\n'
            httpText += ' left *= speed.value / 100.0;'
            httpText += ' right *= speed.value / 100.0;'
            httpText += ' iframe.src = "/set/" + left + "/" + right;\n'
            httpText += '}\n'
            httpText += 'function Off() {\n'
            httpText += ' var iframe = document.getElementById("setDrive");\n'
            httpText += ' iframe.src = "/off";\n'
            httpText += '}\n'
            httpText += 'function Photo() {\n'
            httpText += ' var iframe = document.getElementById("setDrive");\n'
            httpText += ' iframe.src = "/photo";\n'
            httpText += '}\n'
            httpText += '//--></script>\n'
            httpText += '</head>\n'
            httpText += '<body>\n'
            httpText += '<iframe src="/stream" width="100%" height="500" frameborder="0"></iframe>\n'
            httpText += '<iframe id="setDrive" src="/off" width="100%" height="50" frameborder="0"></iframe>\n'
            httpText += '<center>\n'
            httpText += '<button onmousedown="Drive(-1,1)" onmouseup="Off()" style="width:200px;height:100px;"><b>Spin Left</b></button>\n'
            httpText += '<button onmousedown="Drive(1,1)" onmouseup="Off()" style="width:200px;height:100px;"><b>Forward</b></button>\n'
            httpText += '<button onmousedown="Drive(1,-1)" onmouseup="Off()" style="width:200px;height:100px;"><b>Spin Right</b></button>\n'
            httpText += '<br /><br />\n'
            httpText += '<button onmousedown="Drive(0,1)" onmouseup="Off()" style="width:200px;height:100px;"><b>Turn Left</b></button>\n'
            httpText += '<button onmousedown="Drive(-1,-1)" onmouseup="Off()" style="width:200px;height:100px;"><b>Reverse</b></button>\n'
            httpText += '<button onmousedown="Drive(1,0)" onmouseup="Off()" style="width:200px;height:100px;"><b>Turn Right</b></button>\n'
            httpText += '<br /><br />\n'
            httpText += '<button onclick="Photo()" style="width:200px;height:100px;"><b>Save Photo</b></button>\n'
            httpText += '<br /><br />\n'
            httpText += '<input id="speed" type="range" min="0" max="100" value="100" style="width:600px" />\n'
            httpText += '</center>\n'
            httpText += '</body>\n'
            httpText += '</html>\n'
            self.send(httpText)
        elif get_path == '/stream':
            # Streaming frame, set a delayed refresh
            displayDelay = int(1000 / self.GLOBAL_DATA['display_rate'])
            httpText = '<html>\n'
            httpText += '<head>\n'
            httpText += '<script language="JavaScript"><!--\n'
            httpText += 'function refreshImage() {\n'
            httpText += ' if (!document.images) return;\n'
            httpText += ' document.images["rpicam"].src = "cam.jpg?" + Math.random();\n'
            httpText += f' setTimeout("refreshImage()", {displayDelay});\n'
            httpText += '}\n'
            httpText += '//--></script>\n'
            httpText += '</head>\n'
            httpText += f'<body onLoad="setTimeout(\'refreshImage()\', {displayDelay})">\n'
            httpText += '<center><img src="/cam.jpg" style="width:600;height:480;" name="rpicam" /></center>\n'
            httpText += '</body>\n'
            httpText += '</html>\n'
            self.send(httpText)
        else:
            # Unexpected page
            self.send(f'Path : "{get_path}"')

    def send(self, content):
        self.request.sendall(f'HTTP/1.0 200 OK\n\n{content}')


class MonsterWeb:
    _LOG_PATH = os.path.join(LOG_PATH, 'monster_web.log')
    _BASE_LOGGER_NAME = 'examples'
    _LOGGER_NAME = f'{_BASE_LOGGER_NAME}.monster_web'
    _TBORG_LOGGER_NAME = 'examples.tborg'
    WEB_PORT = 80
    """
    int: Port number for the web-page, 80 (default).
    """
    IMAGE_WIDTH = 240
    """
    int: Width of the captured image in pixels
    """
    IMAGE_HEIGHT = 192
    """
    int: Height of the captured image in pixels
    """
    FRAME_RATE = 30
    """
    int: Number of images to capture per second
    """
    DISPLAY_RATE = 10
    """
    int: Number of images to request per second
    """
    PHOTO_DIRECTORY = "/home/{}"
    """
    str: Directory to save photos to
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
    PROCESSOR = None
    RUNNING = True
    WATCHDOG = None
    MAX_POWER = None

    def __init__(self, address: int=0x15, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tb = ThunderBorg(logger_name=self._TBORG_LOGGER_NAME,
                              address=address, log_level=logging.INFO)
        self.camera = None
        self.global_data = {'tb': self.tb,
                            'display_rate': self.DISPLAY_RATE,
                            'photo_directory': self.PHOTO_DIRECTORY,
                            'flipped_amera': self.FLIPPED_CAMERA,
                            'jpeg_quality': self.JPEG_QUALITY,
                            'last_frame': self.LAST_FRAME,
                            'lock_frame': self.LOCK_FRAME,
                            'camera': self.camera,
                            'processor': self.PROCESSOR,
                            'watchdog': self.WATCHDOG,
                            'max_power': self.MAX_POWER,
                            }

        self.tb.set_comms_failsafe(False)
        self.tb.set_led_battery_state(False)
        self.tb.set_both_leds(0, 0, 1)

        # Power settings
        # Total battery voltage to the ThunderBorg
        voltageIn = 1.2 * 10
        # Maximum motor voltage, we limit it to 95% to allow the RPi to get
        # uninterrupted power
        voltageOut = 12.0 * 0.95

        # Setup the power limits
        if voltageOut > voltageIn:
            self.MAX_POWER = 1.0
        else:
            self.MAX_POWER = voltageOut / float(voltageIn)

    def create_image_buffer_frame(self):
        """
        Create the image buffer frame
        """
        # Startup sequence
        self.camera = Picamera2()
        config = picam2.create_video_configuration(
            main={"size": (self.IMAGE_WIDTH, self.IMAGE_HEIGHT),
                  "format": "BGR888"},
            controls={"FrameDurationLimits": (
                int(1_000_000 / self.FRAME_RATE),
                int(1_000_000 / self.FRAME_RATE))})
        self.camera.configure(config)
        self.camera.start()

        print("Setup the stream processing thread")
        self.PROCESSOR = StreamProcessor(self.LAST_FRAME, self.LOCK_FRAME,
                                         self.CAMERA)
        print("Wait ...")
        time.sleep(2)
        captureThread = ImageCapture(self.CAMERA, self.PROCESSOR, self.RUNNING)
        print("Setup the watchdog")
        self.WATCHDOG = Watchdog(self.tb)

        # Run the web server until we are told to close
        try:
            WebServer.GLOBAL_DATA = self.global_data
            httpServer = TCPServer(("0.0.0.0", self.WEB_PORT), WebServer)
        except Exception:
            # Failed to open the port, report common issues
            print("\nFailed to open port {webPort}")
            print("Make sure you are running the script with sudo "
                  "permissions.")
            print("Other problems include running another script with the "
                  "same port.")
            print("If the script was just working recently try waiting a "
                  "minute first.\n")
            # Flag the script to exit
            self.RUNNING = False

        print("Press CTRL+C to terminate the web-server.")

        try:
            while self.RUNNING:
                httpServer.handle_request()
        except KeyboardInterrupt:
            # CTRL+C exit
            print("\nUser shutdown")
        finally:
            # Turn the motors off under all scenarios
            self.tb.halt_motors()
            print("Motors off")

        # Tell each thread to stop, and wait for them to end
        if httpServer is not None:
            httpServer.server_close()

        self.RUNNING = False
        captureThread.join()
        self.PROCESSOR.terminated = True
        self.WATCHDOG.terminated = True
        self.PROCESSOR.join()
        self.WATCHDOG.join()
        self.CAMERA = None
        self.tb.set_led_battery_state(False)
        self.tb.set_both_leds(0, 0, 0)
        self.tb.halt_motors()
        print("Web-server terminated.")


if __name__ == "__main__":
    import traceback
    ret = 0

    try:
        mw = MonsterWeb()
        mw.create_image_buffer_frame()
    except Exception:
        tb = sys.exc_info()[2]
        traceback.print_tb(tb)
        print(f"{sys.exc_info()[0]}: {sys.exc_info()[1]}\n")
        ret = 1

    sys.exit(ret)
