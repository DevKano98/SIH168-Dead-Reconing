import subprocess
import json
import glob

for f in glob.glob("video assets/*.mp4"):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", f]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        info = json.loads(res.stdout)
    except Exception as e:
        print(f"Error parsing {f}: {e}")
        continue
    fmt = info.get("format", {})
    print(f"=== {f} ===")
    print("Duration:", fmt.get("duration"), "seconds")
    print("Size (MB):", round(int(fmt.get("size", 0)) / (1024 * 1024), 2))
    for s in info.get("streams", []):
        st = s.get("codec_type")
        if st == "video":
            w = s.get("width")
            h = s.get("height")
            codec = s.get("codec_name")
            fps = s.get("r_frame_rate")
            print(f"  Video: {codec} {w}x{h} @ {fps} fps")
        elif st == "audio":
            codec = s.get("codec_name")
            sr = s.get("sample_rate")
            ch = s.get("channels")
            print(f"  Audio: {codec} {sr} Hz ({ch} channels)")
