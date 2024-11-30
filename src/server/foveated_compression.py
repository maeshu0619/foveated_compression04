"""
αブレンドによる高解像度エリアの合成は、動画の合成数が増加するにつれて
輝度が高くなるバグを修正することができるが、計算コストが高いため、推奨されない。
result=src1×α+src2×β+γ

    # 高解像度エリアの合成（アルファブレンド）
    high_alpha = high_mask / 255.0
    med_alpha = med_mask / 255.0 * (1.0 - high_alpha)
    low_alpha = 1.0 - high_alpha - med_alpha

    # 合成フレームの計算
    combined_frame = (
        frame_high * high_alpha +
        frame_med * med_alpha +
        frame_low * low_alpha
    ).astype(np.uint8)

よって現在は、条件分岐を使って合成を行っている。
"""
import cv2
import numpy as np
import os

segment_layer_index = 0

def apply_circular_mask(frame, center_x, center_y, radius, resolution_name):
    """
    Applies a circular mask to the frame, making areas outside the circle transparent.
    """
    h, w = frame.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (center_x, center_y), radius, 255, -1)

    # Convert the frame to BGRA to support transparency
    frame_with_alpha = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    frame_with_alpha[mask == 0, 3] = 0  # Set transparency outside the circle

    #print(f"Circular mask applied to {resolution_name} resolution frame.")
    return frame_with_alpha

def save_frames_to_segments(frames_buffer, fps, resolution_name, output_dir, segment_layer_index):
    """
    Save frames in the buffer as a video segment.
    """

    if not frames_buffer:
        print(f"No frames to save for {resolution_name}.")
        return

    os.makedirs(output_dir, exist_ok=True)
    segment_path = os.path.join(output_dir, f"{resolution_name}_segment{segment_layer_index:04d}.mp4")
    
    height, width = frames_buffer[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(segment_path, fourcc, fps, (width, height))

    for frame in frames_buffer:
        video_writer.write(frame)

    video_writer.release()
    print(f"Segment saved: {segment_path}")

def merge_frame(frame_low, frame_med, frame_high, cursor_x, cursor_y):
    # マスクの初期化
    med_mask = np.zeros((frame_low.shape[0], frame_low.shape[1]), dtype=np.uint8)
    high_mask = np.zeros((frame_low.shape[0], frame_low.shape[1]), dtype=np.uint8)

    # マスクの半径設定
    med_radius = 200
    high_radius = 100

    # マスクの作成（円形）
    cv2.circle(med_mask, (cursor_x, cursor_y), med_radius, 255, -1)
    cv2.circle(high_mask, (cursor_x, cursor_y), high_radius, 255, -1)

    # 条件分岐を使って合成
    combined_frame = np.where(
        high_mask[..., np.newaxis] > 0,
        frame_high,
        np.where(med_mask[..., np.newaxis] > 0, frame_med, frame_low)
    )

    return combined_frame
