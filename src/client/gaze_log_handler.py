import os

def load_gaze_log(log_dir, segment_index, fps, duration):
    """
    指定されたセグメントの疑似視線ログを読み込む。

    Parameters:
    - log_dir (str): ログファイルが保存されているディレクトリ
    - segment_index (int): セグメントのインデックス
    - fps (int): フレームレート
    - duration (int): セグメントの長さ（秒）

    Returns:
    - list[tuple]: フレームごとの視線位置 (x, y) のリスト
    """
    log_file = os.path.join(log_dir, f"segment_{segment_index:04d}.txt")
    if not os.path.exists(log_file):
        raise FileNotFoundError(f"視線ログファイルが見つかりません: {log_file}")

    gaze_positions = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Frame") or not line:  # ヘッダー行や空行をスキップ
                continue
            parts = line.split(",")
            if len(parts) != 3:
                continue
            try:
                frame, x, y = map(int, parts)
                gaze_positions.append((x, y))
            except ValueError:
                continue

    expected_frames = fps * duration
    if len(gaze_positions) != expected_frames:
        raise ValueError(f"視線ログが不完全です。期待されるフレーム数: {expected_frames}, 実際のフレーム数: {len(gaze_positions)}")

    return gaze_positions
