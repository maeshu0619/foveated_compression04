import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pygame
from queue import Empty
import os

class PlotWindow:
    def __init__(self, monitor_queue):
        self.monitor_queue = monitor_queue
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))  # Adjust window size for 3x2 grid
        pygame.display.set_caption("Plot Window - Real-time Plot")
        
        # Create a 3x2 grid of subplots
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4), (self.ax5, self.ax6)) = plt.subplots(3, 2, figsize=(10, 8))
        
        self.time_data = []
        self.bandwidth_data = {"sent": [], "recv": []}
        self.jitter_data = []
        self.packet_data = {"TCP": [], "UDP": [], "ICMP": []}
        self.backhaul_delay_data = []
        self.backbone_delay_data = []
        self.traffic_processing_time_data = []

    def update_data(self):
        try:
            data = self.monitor_queue.get_nowait()
            current_time = len(self.time_data)
            self.time_data.append(current_time)

            # Append data for each metric
            self.bandwidth_data["sent"].append(data["sent_bandwidth"])
            self.bandwidth_data["recv"].append(data["recv_bandwidth"])
            self.jitter_data.append(data["jitter"])
            #print(f"TCP Packets: {data['tcp_packets']}, UDP Packets: {data['udp_packets']}, ICMP Packets: {data['icmp_packets']}")
            self.packet_data["TCP"].append(data["tcp_packets"])
            self.packet_data["UDP"].append(data["udp_packets"])
            self.packet_data["ICMP"].append(data["icmp_packets"])
            self.backhaul_delay_data.append(data["backhaul_delay"])
            self.backbone_delay_data.append(data["backbone_delay"])
            self.traffic_processing_time_data.append(data["traffic_processing_time"])

            # Plot bandwidth
            self.ax1.clear()
            self.ax1.plot(self.time_data, self.bandwidth_data["sent"], label="Sent", color="blue")
            self.ax1.plot(self.time_data, self.bandwidth_data["recv"], label="Received", color="green")
            self.ax1.set_title("Bandwidth (MB/s)")
            self.ax1.legend()

            # Plot packet counts
            self.ax2.clear()
            self.ax2.plot(self.time_data, self.packet_data["TCP"], label="TCP", color="orange")
            self.ax2.plot(self.time_data, self.packet_data["UDP"], label="UDP", color="purple")
            self.ax2.plot(self.time_data, self.packet_data["ICMP"], label="ICMP", color="brown")
            self.ax2.set_title("Packet Count")
            self.ax2.legend()

            # Plot jitter
            self.ax3.clear()
            self.ax3.plot(self.time_data, self.jitter_data, label="Jitter", color="red")
            self.ax3.set_title("Jitter (ms)")
            self.ax3.legend()

            # Plot backhaul delay
            self.ax4.clear()
            self.ax4.plot(self.time_data, self.backhaul_delay_data, label="Backhaul Delay", color="cyan")
            self.ax4.set_title("Backhaul Delay (ms)")
            self.ax4.legend()

            # Plot backbone delay
            self.ax5.clear()
            self.ax5.plot(self.time_data, self.backbone_delay_data, label="Backbone Delay", color="yellow")
            self.ax5.set_title("Backbone Delay (ms)")
            self.ax5.legend()

            # Plot traffic processing time
            self.ax6.clear()
            self.ax6.plot(self.time_data, self.traffic_processing_time_data, label="Processing Time", color="magenta")
            self.ax6.set_title("Traffic Processing Time (ms)")
            self.ax6.legend()

            # Adjust layout and save the plot image
            self.fig.tight_layout()
            self.fig.savefig("plot.png")

        except Empty:
            #print("Queue is empty, no data to plot.")
            return

    def render(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            try:
                self.update_data()
                if os.path.exists("Assets/plot.png"):
                    plot_image = pygame.image.load("Assets/plot.png")
                    plot_image = pygame.transform.scale(plot_image, (800, 600))  # Adjust to window size
                    self.screen.blit(plot_image, (0, 0))
                else:
                    print("Plot image not found!")
                    
                pygame.display.flip()
                clock.tick(1)
            except Exception as e:
                print(f"Error in Plot Window: {e}")
        pygame.quit()
