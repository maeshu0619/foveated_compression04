import cv2
import os
import subprocess
import traceback
import datetime
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom
from src.server.foveated_compression import apply_circular_mask, save_frames_to_segments


# グローバルバッファを初期化
frame_buffer = []
frame_buffer_low = []
frame_buffer_med = []
frame_buffer_high = []
segment_index = 0
segment_layer_index = 0

frame_index = 0

def apply_circular_mask(frame, center_x, center_y, radius):
    """
    フレームに円形マスクを適用する関数。円外の部分を黒くする。
    """
    mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
    #frame_height, frame_width = frame.shape[:2]

    '''
    # 中心座標がフレームの範囲内に収まるように調整
    center_x = int(max(0, min(center_x, frame_width - 1)))
    center_y = int(max(0, min(center_y, frame_height - 1)))
    '''

    # 円形マスクを適用
    cv2.circle(mask, (center_x, center_y), radius, 255, -1)
    result = cv2.bitwise_and(frame, frame, mask=mask)
    return result


def save_frame(masked_high, frame_index, output_directory):
    """
    Save a high-resolution masked frame to a specified directory.

    Parameters:
    - masked_high: The high-resolution masked frame (numpy array).
    - frame_index: The index of the frame (used for naming).
    - output_directory: The directory to save the frame (default: "frames/high_frames").
    """
    os.makedirs(output_directory, exist_ok=True)  # Ensure the output directory exists
    frame_path = os.path.join(output_directory, f"frame_{frame_index:04d}.png")
    cv2.imwrite(frame_path, masked_high)
    #print(f"High frame saved: {frame_path}")

def frame_segmented_with_mask(
    frame_low, frame_med, frame_high, gaze_x, gaze_y, fps, segment_dir, segment_duration=2
):
    """
    Applies masks to medium- and high-resolution frames, saves masked frames
    along with low-resolution frames, and generates video segments.
    """
    global frame_index

    # 解像度情報を取得
    #low_height, low_width = frame_low.shape[:2]
    med_height, med_width = frame_med.shape[:2]
    high_height, high_width = frame_high.shape[:2]

    med_height_ratio = med_height / high_height
    #low_height_ratio = low_height / high_height
    med_width_ratio = med_width / high_width
    #low_width_ratio = low_width / high_width
    med_ratio_ave = (med_height_ratio + med_width_ratio) / 2

    # Apply circular masks
    high_radius = 100
    med_radius = 100 #* int(med_ratio_ave)

    masked_high = apply_circular_mask(frame_high, gaze_x, gaze_y, high_radius)
    masked_med = apply_circular_mask(frame_med, int(gaze_x*med_width_ratio), int(gaze_y*med_height_ratio), med_radius)

    '''
    # フレームを保存
    save_frame(frame_high, frame_index, output_directory="frames/original/high_frames")
    save_frame(frame_med, frame_index, output_directory="frames/original/med_frames")
    save_frame(frame_low, frame_index, output_directory="frames/original/low_frames")
    save_frame(masked_high, frame_index, output_directory="frames/circle/high_frames")
    save_frame(masked_med, frame_index, output_directory="frames/circle/med_frames")
    frame_index += 1
    '''

    # Store frames in buffers
    global frame_buffer_low, frame_buffer_med, frame_buffer_high, segment_layer_index
    frame_buffer_low.append(frame_low)
    frame_buffer_med.append(masked_med)
    frame_buffer_high.append(masked_high)

    frames_per_segment = fps * segment_duration
    if len(frame_buffer_low) >= frames_per_segment:
        save_frames_to_segments(frame_buffer_low, fps, "low", segment_dir, segment_layer_index=segment_layer_index)
        save_frames_to_segments(frame_buffer_med, fps, "med", segment_dir, segment_layer_index=segment_layer_index)
        save_frames_to_segments(frame_buffer_high, fps, "high", segment_dir, segment_layer_index=segment_layer_index)

        # Clear buffers
        frame_buffer_low.clear()
        frame_buffer_med.clear()
        frame_buffer_high.clear()

        segment_layer_index += 1

def frame_segmented(combined_frame, fps, segment_dir="segments/segmented_video", segment_duration=2):
    """
    合成フレームをセグメント化し、H.264/AAC形式でエンコードして保存します。

    Args:
        combined_frame (np.ndarray): 合成されたフレーム。
        fps (int): 動画のフレームレート。
        segment_dir (str): セグメントファイルを保存するディレクトリ。
        segment_duration (int): セグメントの長さ（秒単位）。
    """
    global frame_buffer, segment_index

    # セグメントディレクトリを絶対パスに変換
    segment_dir = os.path.abspath(segment_dir)
    os.makedirs(segment_dir, exist_ok=True)  # ディレクトリを作成

    # 回転と反転の処理
    #combined_frame = cv2.flip(combined_frame, 1)
    combined_frame = cv2.rotate(combined_frame, cv2.ROTATE_90_CLOCKWISE)  # 90度時計回り
    combined_frame = cv2.flip(combined_frame, 1)  # 左右反転

    frames_per_segment = fps * segment_duration
    frame_buffer.append(combined_frame)

    # フレームが規定数に達したらセグメントを保存
    if len(frame_buffer) >= frames_per_segment:
        raw_segment_path = os.path.join(segment_dir, f"segment_{segment_index:04d}_raw.mp4")
        encoded_segment_path = os.path.join(segment_dir, f"segment_{segment_index:04d}.mp4")

        # OpenCVを使って未エンコードの動画を保存
        try:
            height, width, _ = frame_buffer[0].shape
            out = cv2.VideoWriter(raw_segment_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
            for frame in frame_buffer:
                out.write(frame)
            out.release()

            print(f"未エンコードセグメントを保存しました: {raw_segment_path}")

            # ファイルの存在確認
            if not os.path.exists(raw_segment_path):
                raise FileNotFoundError(f"未エンコードファイルが見つかりません: {raw_segment_path}")
        except Exception as e:
            print(f"セグメント保存エラー: {raw_segment_path}")
            print(traceback.format_exc())
            frame_buffer.clear()
            return False

        # ffmpegを使ってH.264/AAC形式にエンコード
        try:
            # ffmpegでH.264/AACに変換 + 90度回転
            command = [
                "ffmpeg",
                "-i", raw_segment_path,
                "-vf", "transpose=0",
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "aac",
                "-strict", "experimental",
                encoded_segment_path,
                "-y"
            ]

            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # ffmpegのエラーチェック
            if result.returncode != 0:
                print(f"ffmpegエラー: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, command)

            print(f"エンコード済みセグメントを保存しました: {encoded_segment_path}")
        except Exception as e:
            print(f"エンコード中にエラーが発生しました: {encoded_segment_path}")
            print(traceback.format_exc())
        finally:
            # 一時的な未エンコードファイルを削除
            if os.path.exists(raw_segment_path):
                os.remove(raw_segment_path)

        # フレームバッファをクリアし、次のセグメントの準備
        frame_buffer.clear()
        segment_index += 1
        return True

    return False


def generate_mpd_layer(segment_dir="segments/segmented_video_layer", mpd_path="segments/manifest_layer.mpd", fps=30):
    segment_dir = os.path.abspath(segment_dir)
    mpd_path = os.path.abspath(mpd_path)
    os.makedirs(os.path.dirname(mpd_path), exist_ok=True)

    # MPDの基本構造
    mpd = ET.Element("MPD", attrib={
        "xmlns": "urn:mpeg:dash:schema:mpd:2011",
        "profiles": "urn:mpeg:dash:profile:isoff-on-demand:2011",
        "type": "dynamic",
        "minBufferTime": "PT1.5S",
        "availabilityStartTime": datetime.datetime.utcnow().isoformat() + "Z",
        "publishTime": datetime.datetime.utcnow().isoformat() + "Z"
    })

    period = ET.SubElement(mpd, "Period", attrib={"id": "1", "start": "PT0S"})

    # 解像度とビットレートを定義
    layer_configs = {
        "low": {"resolution": "640x360", "bitrate": "500k"},
        "med": {"resolution": "960x540", "bitrate": "1500k"},
        "high": {"resolution": "1920x1080", "bitrate": "3000k"}
    }

    # 各レイヤーのAdaptationSetとRepresentationを作成
    for layer, config in layer_configs.items():
        adaptation_set = ET.SubElement(period, "AdaptationSet", attrib={
            "mimeType": "video/mp4",
            "codecs": "avc1.42E01E",
            "width": config["resolution"].split("x")[0],
            "height": config["resolution"].split("x")[1],
            "frameRate": str(fps),
            "bandwidth": config["bitrate"]
        })

        representation = ET.SubElement(adaptation_set, "Representation", attrib={
            "id": layer,
            "bandwidth": config["bitrate"],
            "width": config["resolution"].split("x")[0],
            "height": config["resolution"].split("x")[1],
            "frameRate": str(fps)
        })

        segment_list = ET.SubElement(representation, "SegmentList", attrib={
            "timescale": str(fps),
            "duration": str(2 * fps)  # 2秒ごと
        })

        # セグメントリストを作成
        segment_files = sorted(
            [f for f in os.listdir(segment_dir) if f.startswith(f"{layer}_segment") and f.endswith(".mp4")]
        )
        for segment_file in segment_files:
            ET.SubElement(segment_list, "SegmentURL", attrib={"media": f"segmented_video_layer/{segment_file}"})

    # 整形してファイルに書き込む
    rough_string = ET.tostring(mpd, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml_as_string = reparsed.toprettyxml(indent="  ")

    with open(mpd_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml_as_string)

    print(f"Layer Segments MPD ファイルを生成しました: {mpd_path}")