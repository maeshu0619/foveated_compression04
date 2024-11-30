let segments = [];
let currentSegmentIndex = 0;
let isPlaying = false;
let videoPlayer;

// 現在再生中のセグメント名を表示
function updateCurrentSegmentDisplay(segmentName) {
    const currentSegmentDisplay = document.getElementById("currentSegment");
    currentSegmentDisplay.innerText = `現在再生中のセグメント: ${segmentName}`;
}

window.addEventListener("DOMContentLoaded", async () => {
    console.log("ブラウザがロードされました。キャッシュ準備中...");

    // videoPlayer要素を取得
    videoPlayer = document.getElementById("videoPlayer");
    if (!videoPlayer) {
        console.error("videoPlayer要素が見つかりません。");
        return;
    }

    // 動画終了時のイベントリスナーを追加
    videoPlayer.addEventListener("ended", playNextSegment);

    // マニフェストを取得して再生を準備
    setTimeout(async () => {
        await fetchManifest();
        if (segments.length > 1) {
            playNextSegment(); // 再生を開始
        } else {
            console.log("セグメントが不足しています。再生待機中...");
        }
    }, 4000);
});

async function fetchManifest() {
    const response = await fetch("http://localhost:8080/manifest.mpd");
    const text = await response.text();
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(text, "application/xml");
    const segmentUrls = xmlDoc.getElementsByTagName("SegmentURL");

    const newSegments = [];
    for (let segment of segmentUrls) {
        newSegments.push(segment.getAttribute("media"));
    }

    // 新しいセグメントをリストに追加
    const currentLength = segments.length;
    for (let i = currentLength; i < newSegments.length; i++) {
        segments.push(newSegments[i]);
    }

    console.log("セグメントリスト更新:", segments);
}

function playNextSegment() {
    if (currentSegmentIndex < segments.length) {
        const segmentUrl = `http://localhost:8080/${segments[currentSegmentIndex]}`;
        console.log("再生中のセグメント:", segmentUrl);

        // 再生中のセグメント名を更新
        updateCurrentSegmentDisplay(segments[currentSegmentIndex]);

        videoPlayer.src = segmentUrl;
        videoPlayer.play().catch(err => console.error("再生エラー:", err));
        currentSegmentIndex++;
    } else {
        console.log("再生待機: 新しいセグメントを待機中...");
        setTimeout(playNextSegment, 500); // 新しいセグメントが追加されるまで待機
    }
}

setInterval(async () => {
    await fetchManifest();
}, 2000);
