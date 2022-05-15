import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
from gpiozero import MotionSensor
from detect_image import detect_from_image
import time

pir = MotionSensor(4)
camera = picamera.PiCamera(resolution='640x360', framerate=24)

PAGE="""\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body>
<img src="stream.mjpg" width="640" height="360" />
</body>
</html>
"""

motionFound = False

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header(
                'Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

class FrameBuffer(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

def start_video_server():
    global output
    camera.rotation = 0
    motion = 0.0
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    print("Starting video streaming...")
    server.serve_forever()
    # server.server_close()
    output = FrameBuffer()
    camera.start_recording(output, format='mjpeg')
    
    while True:
        pir.wait_for_motion()
        try:
            camera.stop_recording()
            if time.time() - motion > 150:
                # capture...
                print("motion detected", motion)
                time.sleep(1)
                detect_from_image(camera)
                print("detect done")           
                time.sleep(1)
                motion = time.time()
            
            pir.wait_for_no_motion()
            camera.start_recording(output, format='mjpeg')
        except:
            break
    