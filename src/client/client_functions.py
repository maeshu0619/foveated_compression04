import os
import cv2
import datetime
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom
from src.client.gaze_log_handler import load_gaze_log


def combine_segments(low_path, med_path, high_path, output_path):
    """
    複数の解像度のセグメントを合成。
    """
    cap_low = cv2.VideoCapture(low_path)
    cap_med = cv2.VideoCapture(med_path)
    cap_high = cv2.VideoCapture(high_path)
    frame_width = int(cap_low.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap_low.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap_low.get(cv2.CAP_PROP_FPS))

    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))
    
    while True:
        # フレームを読み取る
        ret_low, frame_low = cap_low.read()
        ret_med, frame_med = cap_med.read()
        ret_high, frame_high = cap_high.read()

        # 読み取りが終了した場合
        if not (ret_low and ret_med and ret_high):
            break

        # 解像度を低解像度のサイズに揃える
        frame_med = cv2.resize(frame_med, (frame_width, frame_height), interpolation=cv2.INTER_LINEAR)
        frame_high = cv2.resize(frame_high, (frame_width, frame_height), interpolation=cv2.INTER_LINEAR)

        # 高・中解像度フレームはすでに円形マスクが適応されていると仮定
        combined_frame = np.where(
            (frame_high[..., 0] != 0)[..., np.newaxis],  # 高解像度の非ゼロ部分をチェック
            frame_high,
            np.where(
                (frame_med[..., 0] != 0)[..., np.newaxis],  # 中解像度の非ゼロ部分をチェック
                frame_med,
                frame_low  # 背景として低解像度フレーム
            )
        )

        out.write(combined_frame)

    cap_low.release()
    cap_med.release()
    cap_high.release()
    out.release()
    print(f'Segment saved: {output_path}')


def generate_mpd(segment_dir="segments/segmented_video", mpd_path="segments/manifest.mpd", fps=30, resolution="960x540", bitrate="1500k"):
    """
    MPDファイルを生成。
    """
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
    adaptation_set = ET.SubElement(period, "AdaptationSet", attrib={
        "mimeType": "video/mp4",
        "codecs": "avc1.42E01E",
        "width": resolution.split("x")[0],
        "height": resolution.split("x")[1],
        "frameRate": str(fps),
        "bandwidth": bitrate
    })

    representation = ET.SubElement(adaptation_set, "Representation", attrib={
        "id": "1",
        "bandwidth": bitrate,
        "width": resolution.split("x")[0],
        "height": resolution.split("x")[1],
        "frameRate": str(fps)
    })

    segment_list = ET.SubElement(representation, "SegmentList", attrib={
        "timescale": str(fps),
        "duration": str(2 * fps)  # 2秒ごと
    })

    # セグメントリストを追加
    segment_files = sorted([f for f in os.listdir(segment_dir) if f.endswith(".mp4")])
    for segment_file in segment_files:
        ET.SubElement(segment_list, "SegmentURL", attrib={"media": f"segmented_video/{segment_file}"})

    # 整形してファイルに書き込む
    rough_string = ET.tostring(mpd, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml_as_string = reparsed.toprettyxml(indent="  ")

    with open(mpd_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml_as_string)

    print(f"Combined Segments MPD ファイルを生成しました: {mpd_path}")

def process_segments(layer_dir, output_dir, log_dir, fps, segment_duration, last_index):
    segment_files = sorted([f for f in os.listdir(layer_dir) if f.endswith(".mp4")])
    segment_count = len(segment_files) // 3  # high, med, low
    print(f'Segment count detected in layer_dir: {segment_count}')

    # output_dir に存在する既存のセグメントをチェック
    existing_output_files = sorted([f for f in os.listdir(output_dir) if f.endswith(".mp4")])
    existing_count = len(existing_output_files)
    print(f'Existing segment count in output_dir: {existing_count}')

    new_segments = range(last_index + 1, segment_count)  # 新しいセグメントの範囲を決定

    # 新しいセグメントのみ処理
    for i in range(existing_count, segment_count):
        log_path = os.path.join(log_dir, f"segment_{i:04d}.txt")
        '''
        # 視線ログが存在するか確認
        if not os.path.exists(log_path):
            print(f"Warning: Gaze log not found for segment {i:04d}. Skipping...")
            break
        '''

        # 視線ログを読み取る
        #gaze_log = load_gaze_log(log_dir, i, fps, segment_duration)
        #print(f'gaze log is {gaze_log}')

        # 各解像度のセグメントパス
        low_path = os.path.join(layer_dir, f"low_segment{i:04d}.mp4")
        med_path = os.path.join(layer_dir, f"med_segment{i:04d}.mp4")
        high_path = os.path.join(layer_dir, f"high_segment{i:04d}.mp4")
        output_path = os.path.join(output_dir, f"segment_{i:04d}.mp4")

        # 各解像度のセグメントが存在するか確認
        if not (os.path.exists(low_path) and os.path.exists(med_path) and os.path.exists(high_path)):
            print(f"Warning: Missing segment files for segment {i:04d} in segmented_video_layer directly. Skipping...")
            break

        # セグメントを合成
        print(f"Combining segment {i:04d}...")
        combine_segments(low_path, med_path, high_path, output_path)