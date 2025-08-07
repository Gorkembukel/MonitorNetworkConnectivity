from subprocess import Popen
import threading
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


class TestResult_Wrapper_sub(QObject):
    update_table_for_result_signal = pyqtSignal(object)
    def __init__(self, hostName ):
        super().__init__()
        
        self.hostName = hostName
        self.id = None
        self.interval = None
        self.transfer = None
        self.bitrate = None
        self.retr = None
        self.cwnd = None
        self.omitted = None
        
        self.Client_subproces:Popen = None


    def set_subproces(self,popen:Popen):# Client_subproces bu metot ile popen'i buraya aktarır
        self.Client_subproces = popen
        t = threading.Thread(target=self.task)#BUG
        t.start()
        
        self.update_table_for_result_signal.emit(self)
    def task(self):
        for line in self.Client_subproces.stdout:
            self.parse_iperf3_line(line)
        
    def parse_iperf3_line(self, line):
    # Omitted kontrolü
        print(line)
        self.omitted = '(omitted)' in line
        line = line.replace('(omitted)', '').strip()

        # sender/receiver varsa ayır
        self.stream_type = None
        if 'sender' in line:
            self.stream_type = 'sender'
            line = line.replace('sender', '').strip()
        elif 'receiver' in line:
            self.stream_type = 'receiver'
            line = line.replace('receiver', '').strip()

        # Regex ile ID, interval, transfer, bitrate, retr, cwnd
        
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
            # Geçerli satır değilse alanları boş yap
            self.id = None
            self.interval = None
            self.transfer = None
            self.bitrate = None
            self.retr = None
            self.cwnd = None
            return

        self.id = match.group(1)
        self.interval = match.group(2)
        self.transfer = match.group(3)
        self.bitrate = match.group(4)
        self.retr = match.group(5) if match.group(5) else ''
        self.cwnd = match.group(6) if match.group(6) else ''
