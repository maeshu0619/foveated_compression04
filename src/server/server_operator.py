"""
セグメントが独立してデコードできるため、用意する動画のフレームはIフレームのみにし、P,Bフレームは取り扱わないのが
最も好ましい。しかし、現在は全てのフレームを参照するようになっている。
"""

import pygame
import cv2
import threading
import os
import src.client.browser_launcher as browser_launcher
import random
import time
import numpy as np
import pygetwindow as gw
from src.server.foveated_compression import merge_frame
from src.server.server_function import frame_segmented, generate_mpd_layer, frame_segmented_with_mask
from src.server.mpeg_server import setup_web_server
from src.server.log_writing import log_gaze_positions
from src.client.client_player import create_client_player
from src.client.browser_launcher import open_chrome

class VideoStreaming:
    def __init__(self, input_video, low_res_path, med_res_path, high_res_path):
        self.low_cap = cv2.VideoCapture(low_res_path)
        self.med_cap = cv2.VideoCapture(med_res_path)
        self.high_cap = cv2.VideoCapture(high_res_path)
        self.cap = cv2.VideoCapture(input_video)

        if not self.cap.isOpened():
            raise ValueError(f"動画ファイルを開けませんでした: {input_video}")

        self.window_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.window_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"Video resolution: {self.window_width}x{self.window_height}")

        # MPEG-DASH 用の初期設定
        self.segment_layer_dir = os.path.abspath("segments/segmented_video_layer")  # 絶対パスを設定
        os.makedirs(self.segment_layer_dir, exist_ok=True)
        print(f"レイヤーセグメントディレクトリ: {self.segment_layer_dir}")

        self.fps = 30
        self.frame_counter = 0
        self.gaze_positions = []  # 各フレームごとの疑似視線位置を記録するリスト
        self.segment_index = 0  # セグメント番号を管理

        # サーバとブラウザを別スレッドで起動
        self.start_web_server()
        self.start_browser()

    def start_web_server(self):
        server_thread = threading.Thread(target=setup_web_server, args=("segments",), daemon=True)
        server_thread.start()

    def start_browser(self):
        browser_thread = threading.Thread(target=open_chrome, args=("http://localhost:8080/player.html",), daemon=True)
        browser_thread.start()

    def generate_gaze_position(self, max_speed=15):
        """疑似視線の位置をランダムに決定する関数"""
        # 前回の視線位置を取得
        prev_x = getattr(self, 'gaze_x', self.window_width // 2)
        prev_y = getattr(self, 'gaze_y', self.window_height // 2)

        # 視線が自然に移動する範囲内で次の位置を計算
        self.gaze_x = max(0, min(prev_x + random.randint(-max_speed, max_speed), self.window_width - 1))
        self.gaze_y = max(0, min(prev_y + random.randint(-max_speed, max_speed), self.window_height - 1))

        return self.gaze_x, self.gaze_y

    def run(self):
        #clock = pygame.time.Clock()
        running = True

        while running:
            ret_low, frame_low = self.low_cap.read()
            ret_med, frame_med = self.med_cap.read()
            ret_high, frame_high = self.high_cap.read()

            if not (ret_low and ret_med and ret_high):
                print("Video capture reached the end or encountered an error.")
                time.sleep(1)  # 一時停止してリソースを解放する
                continue  # エラー後もループを継続
            
            # 正しいリサイズ処理（幅, 高さ の順序で指定）
            '''
            frame_low = cv2.resize(frame_low, (self.window_width, self.window_height))
            frame_med = cv2.resize(frame_med, (self.window_width, self.window_height))
            frame_high = cv2.resize(frame_high, (self.window_width, self.window_height))
            '''

            # 疑似視線位置を更新
            gaze_x, gaze_y = self.generate_gaze_position()

            # 各解像度のセグメントを保存
            frame_segmented_with_mask(frame_low, frame_med, frame_high, gaze_x, gaze_y, fps=30, segment_dir='segmented_video_layer', segment_duration=2)

            # 合成フレーム作成
            '''
            try:
                combined_frame = merge_frame(frame_low, frame_med, frame_high, gaze_y, gaze_x) 
            except Exception as e:
                print(f"Error during frame merging: {e}\n")
                break
            
            frame_segmented(combined_frame, self.fps, self.segment_dir)
            '''
            # 2秒ごとにMPDとログを保存
            #print(f'{self.frame_counter}')
            if self.frame_counter >= self.fps * 2:
                #generate_mpd(segment_dir=self.segment_dir, mpd_path=os.path.join("manifest.mpd"))
                generate_mpd_layer(segment_dir=self.segment_layer_dir, mpd_path=os.path.join("manifest_layer.mpd"))
                # 疑似視線ログを保存
                #log_gaze_positions(log_dir="logs/gaze_logs", segment_index=self.segment_index, gaze_positions=self.gaze_positions)
                self.gaze_positions = []  # ログをリセット
                self.segment_index += 1  # 次のセグメントへ

                self.frame_counter = 0

            self.gaze_positions.append((gaze_x, gaze_y))  # ログに追加

            self.frame_counter += 1

            #clock.tick(60)

        self.cap.release()
        self.low_cap.release()
        self.med_cap.release()
        self.high_cap.release()
        #pygame.quit()
        # 終了時にブラウザを閉じる
        browser_launcher.close_chrome()
