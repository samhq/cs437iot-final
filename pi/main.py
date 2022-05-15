import threading
from video_streaming_server import start_video_server
from api_server import start_api_server
# from detector_server import start_detector_server
# from pyngrok import ngrok

vid_srv = threading.Thread(target=start_video_server, daemon=True)
api_srv = threading.Thread(target=start_api_server, daemon=True)
# det_srv = threading.Thread(target=start_detector_server, daemon=True)

vid_srv.start()
api_srv.start()
# det_srv.start()

vid_srv.join()
api_srv.join()
# det_srv.join()

#video_tunnel = ngrok.connect(8000, "http")
#print("Video Server", video_tunnel)
#
#api_tunnel = ngrok.connect(5000, "http")
#print("API Server", api_tunnel)

print("Success, terminating..")
