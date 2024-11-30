import os

def log_gaze_positions(log_dir, segment_index, gaze_positions):
    """
    疑似視線の位置をセグメントごとにログとして記録する関数。
    :param log_dir: ログファイルを保存するディレクトリ
    :param segment_index: セグメント番号
    :param gaze_positions: 各フレームごとの疑似視線位置のリスト [(x1, y1), (x2, y2), ...]
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"segment_{segment_index:04d}.txt")
    
    with open(log_file_path, "w") as log_file:
        log_file.write("Frame, Gaze_X, Gaze_Y\n")
        for frame_index, (gaze_x, gaze_y) in enumerate(gaze_positions):
            log_file.write(f"{frame_index}, {gaze_x}, {gaze_y}\n")
    
    print(f"ログを保存しました: {log_file_path}")
