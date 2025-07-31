import iperf3
from iperf3 import Client

import PyQt5
from PyQt5.QtCore import pyqtSignal
from PyQt5        import QtCore
class Client_Wrapper(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    



    @QtCore.pyqtslot
    def setParameters(self,_blksize = None,
        _server_hostname = None,
        _port = None,
        _num_streams = None,
        _zerocopy = False,
        _omit = None,
        _duration = None,
        _bandwidth = None,
        _protocol = None):

        self.server_hostname    = _server_hostname
        self.port               = _port
        self.num_streams        = _num_streams
        self.zerocopy           = _zerocopy
        self.omit               = _omit
        self.duration           = _duration
        self.bandwidth          = _bandwidth
        self.protocol           = _protocol


if __name__== "__init__":
    #classı test etmek için pencere oluşturmayı düşünüyorum