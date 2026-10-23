from app import render_video
import traceback

try:
    resp = render_video(2)
    print(resp)
except Exception as e:
    traceback.print_exc()
