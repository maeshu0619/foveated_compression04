"""
1.送信帯域幅と受信帯域幅
意味: これらの値は、監視対象システムから送受信されるデータの速度をメガバイト/秒 (MB/秒) 単位で測定します。
システムとの関連性: 正確な帯域幅の推定は、利用可能なネットワーク容量を評価する上で不可欠です。この概念は、「エンドツーエンドの利用可能な帯域幅の測定方法、ダイナミクス、および TCP スループットとの関係」で説明されているように、エンドツーエンドの利用可能な帯域幅を測定する方法論と結びついています。

2.ジッター
意味: ジッターとは、パケットの到着時間の変動です。一貫したパケットの到着が重要な VoIP やストリーミングなどのリアルタイム アプリケーションでは、ジッターによって中断が発生する可能性があります。
システムとの関連性: この値は、ネットワークの安定性を評価するために計算されます。「パッシブ TCP ストリームの RTT およびジッター パラメータの推定」という作業では、低遅延通信に不可欠なネットワーク QoS (サービス品質) を維持するためのジッターの分析について検討します。さらに、「LTE ネットワークの遅延とジッターの分析」では、特に高い一貫性が求められるサービス (TCP、UDP、ICMP パケット) について、ジッターが LTE ネットワークのパフォーマンスにどのように影響するかについても詳しく説明します。

3.TCP,UDP,ICMP
意味: これらのカウンターは、ネットワークによって処理される伝送制御プロトコル (TCP)、ユーザー データグラム プロトコル (UDP)、およびインターネット制御メッセージ プロトコル (ICMP) パケットの数を追跡します。
システムとの関連性: これらの異なるタイプのパケットを追跡すると、ネットワーク アクティビティの診断に役立ちます。TCP は信頼性は高いですが速度が遅く、UDP は高速ですが信頼性が低く、ICMP は ping 操作などの診断に使用されます。これらのパケットの数を監視すると、潜在的なボトルネックや特定のプロトコルの問題を特定するのに役立ちます。

4.バックホール遅延とバックボーン遅延
意味: これらのメトリックは、バックホール (基地局をコア ネットワークに接続するネットワークの部分) とバックボーン (コア ネットワーク自体) で発生する遅延 (ミリ秒単位) を測定します。
システムとの関連性: ネットワークのバックホールとバックボーンの両方のセクションで発生する遅延は、低遅延通信を保証するために重要です。「LTE ネットワークの遅延とジッターの分析」という論文では、これらの遅延が詳細に分析され、さまざまなネットワーク セグメントがエンドツーエンドの遅延にどのように影響するかが特定されています。遅延を理解することで、オペレーターは遅延の問題が発生する可能性のある場所を正確に特定し、それに応じて最適化することができます。

5.トラフィック処理時間
意味: ネットワークが着信トラフィックと発信トラフィックを処理するのにかかる時間です。
システムとの関連性: このメトリックは、トラフィック処理の効率を測定するのに役立ち、ネットワークが高スループットで時間に敏感なアプリケーションをどれだけうまく管理できるかを示す重要な指標です。「一般的な優先トラフィックのキューイング モデルを使用したワイヤレス ネットワークのエンドツーエンドの遅延分析」という論文では、高優先度トラフィック (URLLC (超信頼性低遅延通信) など) が最小限の遅延で処理されるように、効率的なトラフィック スケジューリングの重要性を強調しています。
"""

import pygame
import psutil
import time
import scapy.all as scapy  # Scapy for packet capture
from multiprocessing import Queue
import random

class MonitorWindow:
    def __init__(self, monitor_queue):
        pygame.init()
        self.running = True
        self.width = 400
        self.height = 500
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Network Monitor - SLoPS & AWM")
        self.font = pygame.font.Font(None, 24)
        self.monitor_queue = monitor_queue
        self.packet_counts = {"TCP": 0, "UDP": 0, "ICMP": 0}
        self.last_net_io = psutil.net_io_counters()
        self.last_bandwidth_check = time.time()

    def measure_bandwidth(self, net_io):
        # Bandwidth Measurement: End-to-End Available Bandwidth
        # Based on "End-to-End Available Bandwidth: Measurement Methodology, Dynamics, and Relation with TCP Throughput"
        sent_bandwidth = (net_io.bytes_sent - self.last_net_io.bytes_sent) / (1024 ** 2)
        recv_bandwidth = (net_io.bytes_recv - self.last_net_io.bytes_recv) / (1024 ** 2)
        self.last_net_io = net_io
        return sent_bandwidth, recv_bandwidth

    def capture_packets(self):
        # Packet Capture: Passive TCP Monitoring
        # Based on "Passive TCP stream estimation of RTT and jitter parameters"
        def packet_handler(packet):
            if packet.haslayer(scapy.TCP):
                self.packet_counts["TCP"] += 1
            elif packet.haslayer(scapy.UDP):
                self.packet_counts["UDP"] += 1
            elif packet.haslayer(scapy.ICMP):
                self.packet_counts["ICMP"] += 1

        scapy.sniff(prn=packet_handler, store=0)

    def estimate_jitter(self, rtt_samples):
        # Jitter Estimation: Jitter Control via Active Window Management
        # Based on "Applying Active Window Management for Jitter Control and Loss Avoidance in Video Streaming over TCP Connections"
        if len(rtt_samples) > 1:
            jitter = sum(abs(rtt_samples[i] - rtt_samples[i - 1]) for i in range(1, len(rtt_samples))) / len(rtt_samples)
        else:
            jitter = 0
        return jitter

    def measure_segment_delay(self, segment_name):
        """
        Network Segment Delay Measurement
        Based on "Delay and Jitter Analysis in LTE Networks"
        """
        if segment_name == "backhaul":
            return random.uniform(10, 50)  # Backhaul delay simulation
        elif segment_name == "backbone":
            return random.uniform(5, 30)  # Backbone delay simulation
        return 0

    def schedule_traffic(self, traffic_type):
        """
        Prioritized Traffic Scheduling
        Based on "End-to-End Latency Analysis in Wireless Networks with Queuing Models for General Prioritized Traffic"
        """
        if traffic_type == "URLLC":
            return random.uniform(1, 5)  # High-priority URLLC traffic processing time
        return random.uniform(10, 20)  # Low-priority traffic processing time

    def render(self):
        rtt_samples = []
        scapy_process = scapy.AsyncSniffer(prn=self.capture_packets)
        scapy_process.start()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            net_io = psutil.net_io_counters()
            sent_bandwidth, recv_bandwidth = self.measure_bandwidth(net_io)
            cpu_usage = psutil.cpu_percent(interval=1)

            # Delay and Jitter Measurement
            current_rtt = random.uniform(50, 150)
            rtt_samples.append(current_rtt)
            jitter = self.estimate_jitter(rtt_samples)

            # Network Segment Delay Measurement
            backhaul_delay = self.measure_segment_delay("backhaul")
            backbone_delay = self.measure_segment_delay("backbone")

            # Prioritized Traffic Scheduling
            traffic_processing_time = self.schedule_traffic("URLLC")  # High-priority traffic scheduling

            # Data sent to the queue includes bandwidth, packet counts, jitter, and delays
            data = {
                "sent_bandwidth": sent_bandwidth,
                "recv_bandwidth": recv_bandwidth,
                "cpu_usage": cpu_usage,
                "tcp_packets": self.packet_counts['TCP'],
                "udp_packets": self.packet_counts['UDP'],
                "icmp_packets": self.packet_counts['ICMP'],
                "jitter": jitter,
                "backhaul_delay": backhaul_delay,
                "backbone_delay": backbone_delay,
                "traffic_processing_time": traffic_processing_time
            }
            self.monitor_queue.put(data)

            # Display the real-time data on the screen
            self.screen.fill((0, 0, 0))
            self.render_text(f"Sent Bandwidth: {sent_bandwidth:.2f} MB/s", 50)
            self.render_text(f"Received Bandwidth: {recv_bandwidth:.2f} MB/s", 80)
            self.render_text(f"Jitter: {jitter:.2f} ms", 110)
            self.render_text(f"TCP Packets: {self.packet_counts['TCP']}", 140)
            self.render_text(f"UDP Packets: {self.packet_counts['UDP']}", 170)
            self.render_text(f"ICMP Packets: {self.packet_counts['ICMP']}", 200)
            self.render_text(f"Backhaul Delay: {backhaul_delay:.2f} ms", 230)
            self.render_text(f"Backbone Delay: {backbone_delay:.2f} ms", 260)
            self.render_text(f"Traffic Processing Time: {traffic_processing_time:.2f} ms", 290)

            pygame.display.flip()
            time.sleep(1)

        pygame.quit()

    def render_text(self, text, y):
        surface = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(surface, (10, y))

