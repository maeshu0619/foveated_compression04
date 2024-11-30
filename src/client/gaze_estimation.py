import random
import pygetwindow as gw

def generate_gaze_position(self, max_speed=30):
    """疑似視線の位置をランダムに決定する関数"""
    # Main Windowの位置とサイズを取得
    window = gw.getWindowsWithTitle("Foveated Compression Video Experiment with H.264 Compression System")[0]
    window_x, window_y = window.left, window.top
    window_width, window_height = self.window_width, self.window_height

    # 前回の視線位置を取得
    prev_x, prev_y = getattr(self, 'gaze_x', window_x), getattr(self, 'gaze_y', window_y)

    # 視線が自然に移動する範囲内で次の位置を計算
    self.gaze_x = max(window_x, min(prev_x + random.randint(-max_speed, max_speed), window_x + window_width))
    self.gaze_y = max(window_y, min(prev_y + random.randint(-max_speed, max_speed), window_y + window_height))

    return self.gaze_x, self.gaze_y
