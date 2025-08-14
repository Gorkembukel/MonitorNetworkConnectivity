
from __future__ import annotations
from typing import Dict, Optional, Tuple

import threading
# SENİN MODÜLLERİN (yolu senin yazdığın gibi)
from source.ssH.osStragey import CommandExecutor, Linux, Windows
from source.ssH.paramiko_Client import Client

from paramiko.channel import ChannelFile,ChannelStderrFile 

class Comand_in_Thread(threading.Thread):
    def __init__(self,cmd,stdout,stderr,decode = False ,daemon = True):
        super().__init__( daemon=daemon)
        self.stdout = stdout
        self.stderr = stderr
        self.decode = decode
        self.cmd = cmd
    def run(self):
        
        """
        Client.execute_command çıktısını güvenli biçimde string'e çevir.
        """
        
        stdout, stderr = self.client.execute_command(self.cmd)
        stdout.channel.timeout(0.0)
        stderr.channel.timeout(0.0)
        self.stdout = stdout
        self.stderr = stderr
        if self.decode:
            out = stdout.read().decode(errors="replace") if hasattr(stdout, "read") else str(stdout or "")
            err = stderr.read().decode(errors="replace") if hasattr(stderr, "read") else str(stderr or "")
            return out, err
        

class ClientWrapper:
    """
    Her host için:
    - Client nesnesi
    - CommandExecutor (strategy: Linux/Windows)
    - OS tespiti greeting() ile ve strategy güncelleme
    """
    def __init__(self, hostname: str, username: str, password: str, port: int = 22, osType: str = "linux"):
        self._osType: str = osType  # 'linux' | 'windows' | 'unknown'
        self.__hostname = hostname
        self.__username = username
        self.__password = password
        self.__port = port

        # Not: Client ctor’unun (hostname, username, password, port, osType) aldığını varsaydın; öyle bıraktım.
        self.client = Client(self.__hostname, self.__username, self.__password, self.__port, self._osType)

        # Başlangıçta linux stratejisi ile başla; greeting sonrası değiştirilecek.
        self.executor = CommandExecutor(Linux())

    def _run_cmd(self, cmd: str, decode: bool = True)-> tuple[ChannelFile, ChannelStderrFile]:
        """
        Client.execute_command çıktısını güvenli biçimde string'e çevir.
        """
        
        stdout, stderr = self.client.execute_command(cmd)
        stdout.channel.timeout(0.0)
        stderr.channel.timeout(0.0)
        if decode:
            out = stdout.read().decode(errors="replace") if hasattr(stdout, "read") else str(stdout or "")
            err = stderr.read().decode(errors="replace") if hasattr(stderr, "read") else str(stderr or "")
            return out, err
        return stdout, stderr
    @property
    def hostname(self) -> str:
        return self.__hostname

    @property
    def os_type(self) -> str:
        return self._osType
    @property
    def username(self) -> str:
        return self.__username

    @property
    def is_connected(self) -> bool:
        # Senin Client içinde is_connect alanının olduğuna göre:
        return getattr(self.client, "is_connect", False)

    def connect(self) -> None:
        self.client.connect()

    def close(self) -> None:
        self.client.close()

    def greet_and_set_strategy(self) -> str:
        """
        Client.greeting() çıktısından OS tipini anla ve executor.strategy'yi güncelle.
        - Varsayım: greeting() ya doğrudan 'linux'/'windows' döner ya da çıktıda bu kelimeler geçer.
        """
        raw = self.client.greeting()  # kullanıcı koduna göre: ya str dönecek ya da bir meta bilgisi
        if raw is None:
            guess = "unknown"
        else:
            text = str(raw).lower()
            if "linux" in text:
                guess = "linux"
            elif "windows" in text or "microsoft" in text:
                guess = "windows"
            else:
                guess = "unknown"

        self._osType = guess
        # Executor stratejisini güncelle:
        if guess == "linux":
            self.executor.strategy = Linux()
        elif guess == "windows":
            self.executor.strategy = Windows()
        # unknown ise mevcut strategy'yi değiştirmiyoruz.

        return guess
    
    def open_iperf3_server_on_remote(
        self,
        *,
        port: int = 5201,
        
        
    ) -> tuple[str, str]:
        """
        Uzakta iperf3 server'ı başlatır. OS'e göre doğru komutu üretir ve çalıştırır.
        
        Döndürür: (stdout, stderr)
        """
        

        # 1) osStrategy ile temel komut üret
        base_cmd = self.executor.comand_Iperf3(role="server", port=port)        

        return self._run_cmd(base_cmd)
    
    def open_iperf3_client_on_remote(self):
        pass

    def open_iperf3(self, **kwargs):
        base_cmd = self.executor.comand_Iperf3(**kwargs)        
        stdout,stderr = self._run_cmd(base_cmd)
        #return self._run_cmd(base_cmd)
    def ping_on_remote(self):
        pass

class Client_Controller:
    def __init__(self):
        # hostname -> ClientWrapper
        self._clients: Dict[str, ClientWrapper] = {}
        # NOT: Executor artık wrapper içinde; burada ayrıca global executor tutmuyoruz.

    # ----------------- Yönetim -----------------
    def add_client(self, hostname: str, username: str, password: str, port: int = 22, osType: str = "linux") -> None:
        """Yeni bir ClientWrapper oluşturup ekler."""
        if hostname in self._clients:
            print(f"[!] {hostname} zaten kayıtlı, üzerine yazılıyor.")
        self._clients[hostname] = ClientWrapper(hostname, username, password, port, osType=osType)
        print(f"[+] {hostname} client eklendi.")

    def remove_client(self, hostname: str) -> None:
        cw = self._clients.pop(hostname, None)
        if cw:
            try:
                cw.close()
            except Exception as e:
                print(f"[!] {hostname} kapatılırken hata: {e}")
            print(f"[-] {hostname} client silindi.")
        else:
            print(f"[!] {hostname} bulunamadı.")

    def get_client(self, hostname: str) -> ClientWrapper:
        cw = self._clients.get(hostname)
        if not cw:
            raise KeyError(f"[!] {hostname} bulunamadı.")
        return cw

    def list_clients(self):
        return list(self._clients.keys())

    # ----------------- Bağlantı -----------------
    def connect_all(self) -> None:
        for hostname, cw in self._clients.items():
            try:
                cw.connect()
            except Exception as e:
                print(f"[!] {hostname} bağlanamadı: {e}")

    def close_all(self) -> None:
        for hostname, cw in self._clients.items():
            try:
                cw.close()
            except Exception as e:
                print(f"[!] {hostname} kapatılırken hata: {e}")

    # ----------------- Greeting / OS stratejisi -----------------
    def greet_all(self) -> None:
        """
        Bağlı olan hostları selamla; greeting()’den OS öğren ve
        wrapper.executor.strategy’yi güncelle.
        """
        for hostname, cw in self._clients.items():
            try:
                if cw.is_connected:
                    os_guess = cw.greet_and_set_strategy()
                    print(f"[+] {hostname}: OS='{os_guess}' strategy='{cw.executor.strategy.__class__.__name__}'")
                else:
                    print(f"[!] {hostname} bağlı değil")
            except Exception as e:
                print(f"[!] {hostname} selamlayamadı: {e}")

    # ----------------- Komut yürütme -----------------
    
