# CLI.py

from scapy_pings import ScapyPinger, is_valid_ip
from PingStats import PingStats

class CLI:
    def __init__(self, targets: list[str], duration: int = 10, interval_ms: int = 1000, parallel: bool = True):
        self.targets = [t for t in targets if is_valid_ip(t)]
        self.duration = duration
        self.interval_ms = interval_ms
        self.parallel = parallel
        self.stats_map = {target: PingStats(target) for target in self.targets}

        self.pinger = ScapyPinger(
            targets=self.targets,
            duration=self.duration,
            interval_ms=self.interval_ms
        )

    def run(self):
        if not self.targets:
            print("🚫 No valid targets to ping.")
            return

        print(f"🚀 Starting ping to {len(self.targets)} targets ({'parallel' if self.parallel else 'sequential'})")
        self.pinger.run(parallel=self.parallel, stats_map=self.stats_map)
        self.pinger.wait_for_all()

        self.display_results()

    def display_results(self):
        print("\n📊 Final Ping Statistics:")
        for target, stats in self.stats_map.items():
            summary = stats.summary()
            print(f"\nTarget: {summary['target']}")
            print(f"  Sent        : {summary['sent']}")
            print(f"  Received    : {summary['received']}")
            print(f"  Failed      : {summary['failed']}")
            print(f"  Success Rate: {summary['success_rate']}%")
            print(f"  Avg RTT     : {summary['avg_rtt']} ms")
            print(f"  Min RTT     : {summary['min_rtt']} ms")
            print(f"  Max RTT     : {summary['max_rtt']} ms")
            print(f"  Jitter      : {summary['jitter']} ms")
            print(f"  Last Result : {summary['last_result']}")
