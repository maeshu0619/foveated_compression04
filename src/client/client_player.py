import shutil
import os

def create_client_player(output_dir="segments", mpd_url="http://localhost:8080/manifest.mpd"):
    """
    MPEG-DASH クライアントプレイヤーの HTML と JavaScript ファイルを生成またはコピーします。

    Args:
        output_dir (str): ファイルを保存するディレクトリ。
        mpd_url (str): MPD ファイルの URL。
    """
    # ディレクトリの作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # コピー元とコピー先のファイルパス
    source_html = os.path.join(output_dir, "player.html")
    source_js = os.path.join(output_dir, "player.js")
    dest_html = os.path.join(output_dir, "player.html")
    dest_js = os.path.join(output_dir, "player.js")

    '''
    # コピー元とコピー先のファイルパス
    source_html = "segments/player.html"
    source_js = "segments/player.js"
    dest_html = os.path.join(output_dir, "segments/player.html")
    dest_js = os.path.join(output_dir, "segments/player.js")
    '''
    # ファイルが存在するか確認
    if os.path.exists(source_html) and os.path.exists(source_js):
        # ファイルの中身が空かどうか確認
        if os.path.getsize(source_html) == 0 or os.path.getsize(source_js) == 0:
            print("player.html または player.js の中身が空です。デバッグを終了します。")
            return

        # ファイルが存在し、中身がある場合はコピー
        try:
            shutil.copy(source_html, dest_html)
            shutil.copy(source_js, dest_js)
            print(f"クライアントプレイヤーのファイルをコピーしました: {dest_html}, {dest_js}")
        except Exception as e:
            print(f"ファイルのコピー中にエラーが発生しました: {e}")
            return
    else:
        # ファイルが存在しない場合はデフォルトの内容で生成
        print("player.html または player.js が存在しません。新規に作成します。")

        # HTML コンテンツ
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Foveated Compression Video Streaming with MPEG-DASH Player</title>
            <script src="https://cdn.dashjs.org/latest/dash.all.min.js"></script>
        </head>
        <body>
            <h1>MPEG-DASH Video Player</h1>
            <video id="videoPlayer" controls width="960" height="540"></video>
            <script src="player.js"></script>
        </body>
        </html>
        """

        # JavaScript コンテンツ
        js_content = f"""
        const url = "{mpd_url}";
        const video = document.getElementById('videoPlayer');
        const player = dashjs.MediaPlayer().create();
        player.initialize(video, url, true);
        video.autoplay = true;
        video.muted = true;

        player.updateSettings({
            'streaming': {
                'liveDelay': 3,
                'jumpGaps': true,
                'lowLatencyEnabled': false  // 低遅延モードを無効化
            }
        });

        setInterval(() => {{
            console.log("MPD ファイルを再読み込みします");
            player.attachSource(url + "?t=" + new Date().getTime());
        }}, 2000);
        """

        # HTML ファイルの作成
        with open(dest_html, "w") as html_file:
            html_file.write(html_content)

        # JavaScript ファイルの作成
        with open(dest_js, "w") as js_file:
            js_file.write(js_content)

        print(f"新規にクライアントプレイヤーのファイルを生成しました: {dest_html}, {dest_js}")