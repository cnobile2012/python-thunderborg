#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Creates a web-page interface for the MonsterBorg.
#
__docformat__ = "restructuredtext en"

import ThunderBorg
import time
import sys
import threading
import picamera2
import cv2
import datetime

from socketserver import TCPServer


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
                    self.tb.SetLedShowBattery(True)
                    timed_out = False
                    self.event.clear()
            else:
                if self.event.wait(1):
                    self.event.clear()
                else:
                    # Timed out
                    print("Timed out...")
                    self.tb.SetLedShowBattery(False)
                    self.tb.SetLeds(0, 0, 1)
                    timed_out = True
                    self.tb.MotorsOff()


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
        self.stream = picamera.array.PiRGBArray(global_data['camera'])
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
                        flippedArray = cv2.flip(self.stream.array, -1)
                        retval, thisFrame = cv2.imencode(
                            '.jpg', flippedArray,
                            [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
                        del flippedArray
                    else:
                        retval, thisFrame = cv2.imencode(
                            '.jpg', self.stream.array,
                            [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])

                    self.lock_frame.acquire()
                    self.last_frame = thisFrame
                    self.lock_frame.release()
                finally:
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()


class WebServer(SocketServer.BaseRequestHandler):
    """
    Class used to implement the web server
    """
    GLOBAL_DATA = None

    def handle(self):
        # Get the HTTP request data
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
            self.lock_frame.acquire()
            send_frame = self.last_frame
            self.lock_frame.release()

            if send_frame is not None:
                self.send(send_frame.tostring())
        elif get_path.startswith('/off'):
            # Turn the drives off
            httpText = '<html><body><center>'
            httpText += 'Speeds: 0 %, 0 %'
            httpText += '</center></body></html>'
            self.send(httpText)
            self.tb.MotorsOff()
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
            driveLeft *= self.max_power
            driveRight *= self.max_power
            self.tb.SetMotor1(driveRight)
            self.tb.SetMotor2(driveLeft)
        elif get_path.startswith('/photo'):
            # Save camera photo
            self.lock_frame.acquire()
            captureFrame = self.last_frame
            self.lock_frame.release()
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


class ImageCapture(threading.Thread):
    """
    Image capture thread
    """
    def __init__(self, camera, processor, running, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera = camera
        self.processor = processor
        self.running = running
        self.start()

    def run(self):
        print("Start the stream using the video port.")
        self.camera.capture_sequence(self.TriggerStream(), format='bgr',
                                     use_video_port=True)
        print("Terminating camera processing...")
        self.processor.terminated = True
        self.processor.join()
        print("Processing terminated.")

    # Stream delegation loop
    def TriggerStream(self):
        while self.running:
            if self.processor.event.is_set():
                time.sleep(0.01)
            else:
                yield self.processor.stream
                self.processor.event.set()


class MonsterWeb:
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
    CAMERA = picamera.PiCamera()
    PROCESSOR = None
    RUNNING = True
    WATCHDOG = None
    MAX_POWER = None

    def __init__(self, address: int=0x15, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tb = ThunderBorg.ThunderBorg()
        self.tb.i2cAddress = address  # Board address
        self.tb.Init()
        self.global_data = {'tb': self.tb,
                            'web_ port': self.WEB_PORT,
                            'image_width': self.IMAGE_WIDTH,
                            'image_height': self.IMAGE_HEIGHT,
                            'frame_rate': self.FRAME_RATE,
                            'display_rate': self.DISPLAY_RATE,
                            'photo_directory': self.PHOTO_DIRECTORY,
                            'flipped_camera': self.FLIPPED_CAMERA,
                            'jpeg_quality': self.JPEG_QUALITY,
                            'last_frame': self.LAST_FRAME,
                            'lock_frame': self.LOCK_FRAME,
                            'camera': self.CAMERA,
                            'processor': self.PROCESSOR,
                            'running': self.RUNNING,
                            'watchdog': self.WATCHDOG,
                            'max_power': self.MAX_POWER,
                            }

        if not self.tb.foundChip:
            boards = ThunderBorg.ScanForThunderBorg()

            if len(boards) == 0:
                print("No ThunderBorg found, check you are attached :)")
            else:
                print(f"No ThunderBorg at address {self.tb.i2cAddress:02X}, "
                      "but we did find boards:")

                for board in boards:
                    print(f"    {board:02X} ({board})")

                print("If you need to change the I²C address change the "
                      "setup line so it is correct, e.g.")
                print("self.tb.i2cAddress = 0x{boards[0]:02X}")

            sys.exit()

        self.tb.SetCommsFailsafe(False)
        self.tb.SetLedShowBattery(False)
        self.tb.SetLeds(0, 0, 1)

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
        print("Setup camera")
        self.camera.resolution = (self.IMAGE_WIDTH, self.IMAGE_HEIGHT)
        self. camera.framerate = self.FRAME_RATE

        print("Setup the stream processing thread")
        self.processor = StreamProcessor(self.last_frame, self.lock_frame,
                                         self.camera)
        print("Wait ...")
        time.sleep(2)
        captureThread = ImageCapture(self.camera, self.processor, self.running)
        print("Setup the watchdog")
        self.watchdog = Watchdog(self.tb)

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
            self.running = False

        print("Press CTRL+C to terminate the web-server.")

        try:
            while self.RUNNING:
                httpServer.handle_request()
        except KeyboardInterrupt:
            # CTRL+C exit
            print("\nUser shutdown")
        finally:
            # Turn the motors off under all scenarios
            self.tb.MotorsOff()
            print("Motors off")

        # Tell each thread to stop, and wait for them to end
        if httpServer is not None:
            httpServer.server_close()

        self.running = False
        captureThread.join()
        self.processor.terminated = True
        self.watchdog.terminated = True
        self.processor.join()
        self.watchdog.join()
        self.camera = None
        self.tb.SetLedShowBattery(False)
        self.tb.SetLeds(0, 0, 0)
        self.tb.MotorsOff()
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
