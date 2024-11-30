import os
import subprocess

def h264_compression(input_video):
    try:
        low_res_output = "h264_outputs/low_res.mp4"
        med_res_output = "h264_outputs/med_res.mp4"
        high_res_output = "h264_outputs/high_res.mp4"

        # ディレクトリのチェックと作成
        if not os.path.exists("h264_outputs"):
            try:
                subprocess.run(["mkdir", "-p", "h264_outputs"], shell=True, check=True)
                print('"h264_outputs" directory is meked')
            except subprocess.CalledProcessError as e:
                print(f"Error creating h264_outputs directory: {e}")
        else:
            print('"h264_outputs" already exists')

        # FFmpeg コマンドの実行
        commands = [
            {
                "output": low_res_output,
                "cmd": [
                    "ffmpeg", "-y", "-i", input_video,
                    "-vf", "scale=480:270", "-c:v", "libx264", "-crf", "50", "-preset", "ultrafast",
                    "-tune", "zerolatency", low_res_output
                ]
            },
            {
                "output": med_res_output,
                "cmd": [
                    "ffmpeg", "-y", "-i", input_video,
                    "-vf", "scale=640:360", "-c:v", "libx264", "-crf", "30", "-preset", "ultrafast",
                    "-tune", "zerolatency", med_res_output
                ]
            },
            {
                "output": high_res_output,
                "cmd": [
                    "ffmpeg", "-y", "-i", input_video,
                    "-vf", "scale=1920:1080", "-c:v", "libx264", "-crf", "1", "-preset", "ultrafast",
                    "-tune", "zerolatency", high_res_output
                ]
            }
        ]

        for command in commands:
            try:
                print(f"Running FFmpeg for {command['output']}")
                result = subprocess.run(command["cmd"], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"FFmpeg failed for {command['output']} with error: {result.stderr}")
                else:
                    print(f"Successfully created {command['output']}")
            except Exception as e:
                print(f"Exception while running FFmpeg for {command['output']}: {e}")

        return low_res_output, med_res_output, high_res_output
    except Exception as e:
        print(f"H.264 Compression failed: {e}")
        raise
