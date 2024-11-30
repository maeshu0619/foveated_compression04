import pygame
import multiprocessing
import atexit
import signal
import os
import time
from src.server.h264_compression import h264_compression
from src.server.server_operator import VideoStreaming
from src.monitor_window import MonitorWindow
from src.plot_window import PlotWindow
from src.client.browser_launcher import close_chrome
from src.client.client_operator import VidepPlayback

def start_monitor_window(monitor_queue):
    monitor = MonitorWindow(monitor_queue)
    monitor.render()

def start_plot_window(monitor_queue):
    plot = PlotWindow(monitor_queue)
    plot.render()
    
def handle_exit(signum, frame):
    """
    シグナル捕捉時にクリーンアップ処理を呼び出す。
    """
    print(f"終了シグナル({signum})を受信しました。クリーンアップを開始します...")
    close_chrome()
    os._exit(0)

# プログラム終了時に呼び出される関数を登録
atexit.register(close_chrome)
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def start_video_streaming(input_video, low_res_path, med_res_path, high_res_path):
    """
    VideoStreaming の実行
    """
    video_streaming = VideoStreaming(input_video, low_res_path, med_res_path, high_res_path)
    video_streaming.run()

def start_video_playback(layer_dir):
    """
    VideoPlayback の実行
    """
    client_operator = VidepPlayback(layer_dir=layer_dir)
    client_operator.run()

if __name__ == "__main__":
    pygame.init()
    monitor_queue = multiprocessing.Queue()
    input_video = "Assets/Snow.mp4"

    try:
        # フォビエイテッド圧縮を実行
        low_res_path, med_res_path, high_res_path = h264_compression(input_video)
        print(f"H.264 Compression completed successfully.")
    except Exception as e:
        print(f"Error during H.264 Compression: {e}")
        exit(1)

    # Monitor と Plot ウィンドウのプロセスを開始
    '''
    monitor_process = multiprocessing.Process(target=start_monitor_window, args=(monitor_queue,))
    monitor_process.start()

    plot_process = multiprocessing.Process(target=start_plot_window, args=(monitor_queue,))
    plot_process.start()
    '''
    
    '''
    # セグメントディレクトリの作成
    segment_dir="segments/segmented_video"
    if not os.path.exists(segment_dir):
        os.makedirs(segment_dir)
        print(f"ディレクトリを作成しました: {segment_dir}")
    else:
        print(f"ディレクトリが既に存在しています： {segment_dir}")
    '''

    
    # Streaming の初期化と実行
    # マルチプロセスで Streaming と Playback を実行
    try:
        video_streaming_process = multiprocessing.Process(
            target=start_video_streaming,
            args=(input_video, low_res_path, med_res_path, high_res_path)
        )
        video_playback_process = multiprocessing.Process(
            target=start_video_playback,
            args=("segments/segmented_video_layer",)
        )

        # プロセス開始
        video_streaming_process.start()
        video_playback_process.start()

        # メインループで待機
        print("Press Ctrl+C to exit.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting program...")
        video_streaming_process.terminate()
        video_playback_process.terminate()
        pygame.quit()

    # プロセスの終了
    '''
    monitor_process.terminate()
    plot_process.terminate()
    pygame.quit()
    '''    

    '''
    print("Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)  # プログラムを待機状態に保つ
    except KeyboardInterrupt:
        print("Exiting program...")
        close_chrome()
        pygame.quit()
    ''' 