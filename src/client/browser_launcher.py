import webbrowser
import subprocess
import platform
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# グローバル変数
driver = None

#global chrome_process

def open_chrome(url="http://localhost:8080/player.html"):
    """
    Chrome ブラウザで指定された URL を自動的に開く関数。

    Args:
        url (str): 開く URL（デフォルトは MPEG-DASH プレイヤーの URL）。
    """
    global chrome_process
    chrome_path = ""

    if platform.system() == "Windows":
        chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    elif platform.system() == "Darwin":
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif platform.system() == "Linux":
        chrome_path = "/usr/bin/google-chrome"

    if os.path.exists(chrome_path):
        print(f'Chrome起動中...\n')
        chrome_process = subprocess.Popen([chrome_path, "--enable-logging", "--v=1", url])
    else:
        print(f'Chromeが見つかりません')
        chrome_process = webbrowser.open(url)

def close_chrome():
    """Chromeで開いた指定のタブを閉じる関数"""
    global driver
    if driver:
        # 現在開いているタブのURLを取得
        current_url = driver.current_url
        print(f"現在のURL: {current_url}")
        
        # 指定のURLが開かれている場合は閉じる
        if "http://localhost:8080/player.html" in current_url:
            driver.quit()
            print("Chrome タブを閉じました")
        else:
            print("指定のタブは開かれていません")
    else:
        print("Chromeは起動していません")
