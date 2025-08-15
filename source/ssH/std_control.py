import threading
import time
from typing import Optional, Dict
from PyQt5.QtCore import QObject, pyqtSignal
from paramiko.channel import ChannelFile, ChannelStderrFile


class Reader(threading.Thread):
    """
    Tek bir stream (stdout/stderr çifti) için okuma thread'i.
    """
    def __init__(self, owner: "STD_object", name: str, stdout: ChannelFile, stderr: ChannelStderrFile, poll: float = 0.05):
        super().__init__(daemon=True)
        self.owner = owner
        self.name = name
        self.stdout = stdout
        self.stderr = stderr
        self.poll = poll
        self._stop = threading.Event()
        
    def stop(self):
        self._stop.set()

    def run(self):
        ch = self.stdout.channel
        cherr = self.stderr.channel
        ch.settimeout(0.0)
        cherr.settimeout(0.0)
        try:
            while not self._stop.is_set():
                any_data = False

                # STDOUT
                if ch.recv_ready():
                    data = ch.recv(4096).decode(self.owner._encoding, errors="replace")
                    if data:
                        self.owner._append_out(self.name, data)
                        self.owner._emit_stdout_chunk(self.name, data)
                        print(f"[{self.name} OUT] {data}", end="", flush=True)
                        any_data = True

                # STDERR
                if ch.recv_stderr_ready():
                    data_err = ch.recv_stderr(4096).decode(self.owner._encoding, errors="replace")
                    if data_err:
                        self.owner._append_err(self.name, data_err)
                        self.owner._emit_stderr_chunk(self.name, data_err)
                        print(f"[{self.name} ERR] {data_err}", end="", flush=True)
                        any_data = True

                # İş bitti mi?
                if ch.exit_status_ready():
                    # Kalanı boşalt
                    while ch.recv_ready():
                        chunk = ch.recv(4096).decode(self.owner._encoding, errors="replace")
                        if chunk:
                            self.owner._append_out(self.name, chunk)
                            self.owner._emit_stdout_chunk(self.name, chunk)
                            print(f"[{self.name} OUT] {chunk}", end="", flush=True)
                    while ch.recv_stderr_ready():
                        chunk = ch.recv_stderr(4096).decode(self.owner._encoding, errors="replace")
                        if chunk:
                            self.owner._append_err(self.name, chunk)
                            self.owner._emit_stderr_chunk(self.name, chunk)
                            print(f"[{self.name} ERR] {chunk}", end="", flush=True)

                    # exit status / done
                    try:
                        code = ch.recv_exit_status()
                    except Exception:
                        code = None
                    self.owner._set_exit_status(self.name, code)
                    self.owner._set_done(self.name)
                    break

                if not any_data:
                    time.sleep(self.poll)
        finally:
            # Bu stream'e bağlı reader referansını temizle (yeniden başlatılabilsin)
            st = self.owner._streams.get(self.name)
            if st and st.get("reader") is self:
                st["reader"] = None


class STD_object(QObject):
    """
    Birden çok komut/stream'i eşzamanlı yönetir.
    Her stream'in ayrı stdout/stderr buffer'ı ve Reader thread'i vardır.
    """
    # GUI tarafında ayırt etmek için stream adıyla yayınlıyoruz
    stdout_chunk = pyqtSignal(str, str)  # (stream_name, chunk)
    stderr_chunk = pyqtSignal(str, str)  # (stream_name, chunk)
    stdout_to_PingStat = pyqtSignal(object,str,str)#mainwindow da pingparser obje oluşturulan yeri tetikleyecek
    def __init__(self,mainwindow,clientWrapper,encoding: str = "utf-8", max_buffer: Optional[int] = None):
        super().__init__()
        self._encoding = encoding
        self._max_buffer = max_buffer
        self.clientWrapper = clientWrapper
        self.mainwindow = mainwindow
        self.stdout_to_PingStat.connect(self.mainwindow.start_ping_parser)#TODO sakat yer
        # name -> {
        #   "stdin": ChannelFile | None,
        #   "stdout": ChannelFile,
        #   "stderr": ChannelStderrFile,
        #   "out_buf": str,
        #   "err_buf": str,
        #   "reader": Reader | None,
        #   "done": threading.Event,
        #   "exit_status": Optional[int]
        # }
        self._streams: Dict[str, Dict] = {}

    # ------- Stream yaşam döngüsü -------
    def register_stream(self, name: str, *, stdout: ChannelFile, stderr: ChannelStderrFile) -> None:
        self._streams[name] = {            
            "stdout": stdout,
            "stderr": stderr,
            "out_buf": "",
            "err_buf": "",
            "reader": None,
            "done": threading.Event(),
            "exit_status": None,
        }

    def start(self, name: str, reset_buffers: bool = False) -> None:
        st = self._require(name)
        # Eski reader varsa durdur
        if st["reader"] is not None and st["reader"].is_alive():
            st["reader"].stop()
            st["reader"].join(timeout=1.0)
        st["reader"] = None

        if reset_buffers:
            st["out_buf"] = ""
            st["err_buf"] = ""

        reader = Reader(owner=self, name=name, stdout=st["stdout"], stderr=st["stderr"])
        st["reader"] = reader
        reader.start()

    def stop(self, name: str) -> None:
        st = self._require(name)
        if st["reader"] is not None:
            st["reader"].stop()
            st["reader"].join(timeout=1.0)
            st["reader"] = None

    def unregister_stream(self, name: str) -> None:
        # Kaynakları kapatmak istersen burada close() da edebilirsin
        self.stop(name)
        self._streams.pop(name, None)

    # ------- Buffer erişimi -------
    def stdout_text(self, name: str) -> str:
        return self._require(name)["out_buf"]

    def stderr_text(self, name: str) -> str:
        return self._require(name)["err_buf"]

    def is_done(self, name: str) -> bool:
        return self._require(name)["done"].is_set()

    def exit_status(self, name: str) -> Optional[int]:
        return self._require(name)["exit_status"]

    # ------- İç yardımcılar (Reader burayı çağırır) -------
    def _append_out(self, name: str, text: str) -> None:
        st = self._require(name)
        if self._max_buffer is None:
            st["out_buf"] += text
        else:
            st["out_buf"] = (st["out_buf"] + text)[-self._max_buffer:]

    def _append_err(self, name: str, text: str) -> None:
        st = self._require(name)
        if self._max_buffer is None:
            st["err_buf"] += text
        else:
            st["err_buf"] = (st["err_buf"] + text)[-self._max_buffer:]

    def _set_done(self, name: str) -> None:
        self._require(name)["done"].set()

    def _set_exit_status(self, name: str, code: Optional[int]) -> None:
        self._require(name)["exit_status"] = code

    def _emit_stdout_chunk(self, name: str, chunk: str) -> None:
        if name =="ping":
            
            """target = "1.1.1.1"   # elinde yoksa bir default
            self.stdout_to_PingStat.emit(self.clientWrapper, target, chunk)"""

        self.stdout_chunk.emit(name, chunk)

    def _emit_stderr_chunk(self, name: str, chunk: str) -> None:
        self.stderr_chunk.emit(name, chunk)

    def _require(self, name: str) -> Dict:
        st = self._streams.get(name)
        if st is None:
            raise KeyError(f"Stream '{name}' kayıtlı değil.")
        return st
