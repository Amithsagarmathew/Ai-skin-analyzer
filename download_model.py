import urllib.request
import ssl
import os

url = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
path = r'c:\projects\LCC\Skin Care\project\face_landmarker.task'

print(f"Downloading model from {url}...")
try:
    # Bypass SSL if needed (sometimes helps in restricted envs)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    with urllib.request.urlopen(url, context=ctx) as response, open(path, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
    print(f"Downloaded to {path} ({os.path.getsize(path)} bytes)")
except Exception as e:
    print(f"Download Error: {e}")
