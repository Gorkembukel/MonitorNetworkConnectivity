
import subprocess

from source.Iperf.iperf_TestResult_Wrapper import TestResult_Wrapper_sub
from iperf3 import Client

valid_fields = {
            "server_hostname",
            "port",
            "num_streams",
            "zerocopy",
            "omit",
            "duration",
            "bandwidth",
            "protocol",
            "blksize",
            "bind_address",
            "reversed"
        }
class Client_subproces():
    def __init__(self, iperWindow=None, **clientKwargs):
        super().__init__()
        self.iperWindow = iperWindow
        self.clientKwargs = clientKwargs
        #bu kısım geçici, tablonun burayı görmesi lazım ki arayüzde listelensin
        self.client = Client()
        for k, v in self.clientKwargs.items():
            if k in valid_fields:
                setattr(self.client, k, v)
            else:
                print(f"⚠️  Uyarı: iperf3.Client '{k}' parametresini tanımıyor, atlandı.")


        self.client_HostName = self.clientKwargs.get("server_hostname")
        self.testresultWrapper = TestResult_Wrapper_sub(hostName=self.client_HostName)
        self.testresultWrapper.update_table_for_result_signal.connect(self.iperWindow.update_result_table)#si


    def start_iperf(self):
        # Başlangıç komutu
        cmd = ["iperf3", "-c", self.clientKwargs.get("server_hostname")]

        # Optional parametreler
        if self.clientKwargs.get("port"):
            cmd += ["-p", str(self.clientKwargs["port"])]
        if self.clientKwargs.get("num_streams"):
            cmd += ["-P", str(self.clientKwargs["num_streams"])]
        if self.clientKwargs.get("zerocopy"):
            cmd += ["--zerocopy"]
        if self.clientKwargs.get("omit"):
            cmd += ["--omit", str(self.clientKwargs["omit"])]
        if self.clientKwargs.get("duration"):
            cmd += ["-t", str(self.clientKwargs["duration"])]
        if self.clientKwargs.get("bandwidth"):
            cmd += ["-b", f"{self.clientKwargs['bandwidth']}K"]
        if self.clientKwargs.get("protocol") == "UDP":
            cmd += ["-u"]
        if self.clientKwargs.get("blksize"):
            cmd += ["-l", str(self.clientKwargs["blksize"])]

        if self.clientKwargs.get("reversed"):
            if self.clientKwargs["reversed"]:
                cmd += ["-R"]
       

        # Force flush output
        cmd += ["-V"]# detailed info
        cmd += ["--forceflush"]

        # Komutu yazdırmak istersen (debug için)
        print("Running command:", " ".join(cmd))

        # subprocess başlat
        self.testresultWrapper.set_subproces(subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        return self
    def _del__(self):
        print(f"🗑 Siliniyor: {self.clientKwargs.get('server_hostname')}")