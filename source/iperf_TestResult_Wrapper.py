from dataclasses import dataclass
from subprocess import Popen
import threading
from typing import List
import iperf3,re

from iperf3 import TestResult

from PyQt5.QtCore import QObject, pyqtSignal


class TestResult_Wrapper(QObject):
    update_table_for_result_signal = pyqtSignal(object)
    def __init__(self, hostName ):
        super().__init__()
        
        

        
        self.hostName = hostName

        self.TestResult:TestResult = None


    def setResult(self,result:TestResult):
        self.TestResult = result
        self.update_table_for_result_signal.emit(self)






@dataclass
class StreamInfo:
    id: str = None
    interval: str = None
    transfer: str = None
    bitrate: str = None
    retr: str = None
    cwnd: str = None
    stream_type: str = None
    omitted: bool = False

    local_cpu_percent: str = None
    local_cpu_user_sys: str = None
    remote_cpu_percent: str = None
    remote_cpu_user_sys: str = None

    
class TestResult_Wrapper_sub(QObject):
    update_table_for_result_signal = pyqtSignal(object)
    def __init__(self, hostName ):
        super().__init__()
        
        self.streams: List[StreamInfo] = []
        self.hostName = hostName
        self.Client_subproces:Popen = None

        self.local_ip = None
        self.local_port =None
        self.remote_ip = None
        self.remote_port = None

    def set_subproces(self,popen:Popen):# Client_subproces bu metot ile popen'i buraya aktarır
        self.Client_subproces = popen
        t = threading.Thread(target=self.task)#BUG
        t.start()
        
        self.update_table_for_result_signal.emit(self)
    def task(self):
        for line in self.Client_subproces.stdout:
            self.parse_iperf3_line(line)
        
    def parse_iperf3_line(self, line):
        cpu_pattern = re.compile(
        r"CPU Utilization: local/sender ([\d\.]+%) \(([\d\.%u/\.%s]+)\), "
        r"remote/receiver ([\d\.]+%) \(([\d\.%u/\.%s]+)\)"
        )
        cpu_match = cpu_pattern.search(line)
        if cpu_match and self.streams:
            last_stream = self.streams[-1]  # son stream nesnesi

            last_stream.local_cpu_percent = cpu_match.group(1)
            last_stream.local_cpu_user_sys = f"({cpu_match.group(2)})"
            last_stream.remote_cpu_percent = cpu_match.group(3)
            last_stream.remote_cpu_user_sys = f"({cpu_match.group(4)})"
            return# cpu match olduktan sonra başka bilgi olmayacak zaten. diğerlerini aramaya gerek yok
        
        #line içinde ip ve port bilgileri varsa al
        connection_pattern = re.compile(
        r"local ([\d\.]+) port (\d+) connected to ([\d\.]+) port (\d+)"
    )
        connection_match = connection_pattern.search(line)
        if connection_match:
            
            self.local_ip    = connection_match.group(1)
            self.local_port  = connection_match.group(2)
            self.remote_ip   = connection_match.group(3)
            self.remote_port = connection_match.group(4)
            
            print(f"📡 Local IP   : {self.local_ip}")
            print(f"📍 Local Port : {self.local_port}")
            print(f"🌐 Remote IP  : {self.remote_ip}")
            print(f"🛰  Remote Port: {self.remote_port}")
            return

        self.omitted = '(omitted)' in line
        line = line.replace('(omitted)', '').strip()

        stream_type = None
        if 'sender' in line:
            stream_type = 'sender'
            line = line.replace('sender', '').strip()
        elif 'receiver' in line:
            stream_type = 'receiver'
            line = line.replace('receiver', '').strip()

        pattern = re.compile(
            r'\[\s*(\d+)\s*\]\s+'
            r'(\d+\.\d+-\d+\.\d+\s+sec)\s+'
            r'(\d+\s+\w+Bytes)\s+'
            r'(\d+\s+\w+bits/sec)\s+'
            r'(\d+)?\s*'
            r'(\d+\s+\w+Bytes)?'
        )

        match = pattern.search(line)
        if not match:
            return

        stream = StreamInfo(
            id=match.group(1),
            interval=match.group(2),
            transfer=match.group(3),
            bitrate=match.group(4),
            retr=match.group(5) if match.group(5) else '',
            cwnd=match.group(6) if match.group(6) else '',
            stream_type=stream_type,
            omitted=self.omitted
        )

        self.streams.append(stream)
        


    def print_all_stream(self):
        for stream in self.streams:
            self.print_stream(stream=stream)
    def print_stream(self, stream: StreamInfo):
        print("---- Yeni Stream Bilgisi ----")
        print(f"ID        : {stream.id}")
        print(f"Interval  : {stream.interval}")
        print(f"Transfer  : {stream.transfer}")
        print(f"Bitrate   : {stream.bitrate}")
        print(f"Retr      : {stream.retr}")
        print(f"CWND      : {stream.cwnd}")
        print(f"Stream    : {stream.stream_type}")
        print(f"Omitted   : {stream.omitted}")
        print(f"local cpu   : {stream.local_cpu_percent}")
        print(f"remote  cpu   : {stream.remote_cpu_percent}")
        print("-----------------------------\n")
    def __del__(self):
        print(f"❌ TestResult_Wrapper_sub siliniyor: {self.hostName}")