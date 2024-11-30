import os
import time
from src.client.client_functions import combine_segments, generate_mpd, process_segments
#from src.client.gaze_log_handler import load_gaze_log

class VidepPlayback:
    def __init__(self, layer_dir = "segments/segmented_video_layer"):
        # セグメントディレクトリ
        self.output_dir = os.path.abspath("segments/segmented_video")  # 絶対パスを設定
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"合成セグメントディレクトリ: {self.output_dir}")

        self.layer_dir = "segments/segmented_video_layer"
        #self.output_dir = "segments/segmented_video"
        self.mpd_path = os.path.abspath("segments/manifest.mpd")  # 完全パスで保存
        self.mpd_layer_path = "segments/manifest_layer.mpd"
        self.log_dir = "segments/logs/gaze_logs"
        self.segment_duration = 2
        self.fps = 30
        #self.frame_counter = 0
        self.last_segment_index = -1  # 最後に処理したセグメントのインデックス
        #os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        running = True
        start_time = time.time()  # 処理開始時間の記録

        while running:
            # 2秒ごとにMPDとログを保存
            elapsed_time = time.time() - start_time  # 経過時間の計算
            if elapsed_time >= self.segment_duration:  # 2秒経過時に処理を実行
                try:
                    process_segments(
                        layer_dir=self.layer_dir,
                        output_dir=self.output_dir,
                        log_dir=self.log_dir,
                        fps=self.fps,
                        segment_duration=self.segment_duration,
                        last_index=self.last_segment_index
                    )
                    generate_mpd(
                        segment_dir=self.output_dir,
                        mpd_path=self.mpd_path,
                        fps=self.fps,
                        resolution="960x540",
                        bitrate="1500k"
                    )
                    #print("Combined Segments MPD generation completed.")
                    self.frame_counter = 0  # フレームカウンターをリセット
                except Exception as e:
                    print(f'Segments Combining or Combined Segments MPD Generating faled: {e}')
                    break
                start_time = time.time()  # 処理後に時間をリセット

            time.sleep(0.01)  # 短いウェイトで負荷を軽減
            #self.frame_counter += 1