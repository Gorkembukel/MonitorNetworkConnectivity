import iperf3

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
        