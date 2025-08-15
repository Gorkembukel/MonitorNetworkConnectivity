# osStragey.py  (senin modül adınla uyumlu)
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

import shlex  # Linux tarafında güvenli kaçış için


class CommandExecutor:  # ssh komutları, işletim sistemi bazlı strategy değişimi
    """
    Context: Stratejiyi tutar; komut oluşturma isteklerini stratejiye yönlendirir.
    """

    def __init__(self, strategy: "Strategy") -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> "Strategy":
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: "Strategy") -> None:
        self._strategy = strategy

    def comand_Iperf3(self, **kwargs) -> str:
        """OS'e uygun iperf3 komutu üretir (server/client)."""
        return self._strategy.setIperf3(**kwargs)

    def command_Ping(self, **kwargs) -> str:
        """OS'e uygun ping komutu üretir."""
        return self._strategy.setPing(**kwargs)


class Strategy(ABC):
    """
    Tüm stratejiler aynı imza ile komut döndürür; OS'e göre içerik değişir.
    """

    @abstractmethod
    def setIperf3(
        self,
        *,
        role: str = "client",                 # "client" | "server"
        server: Optional[str] = None,         # client ise gerekli
        port: Optional[int] = 5201,
        duration: Optional[int] = None,       # saniye
        parallel: Optional[int] = None,       # -P
        reverse: bool = False,                # -R (client'tan server'a)
        udp: bool = False,                    # -u
        bandwidth: Optional[str] = None,      # "100M", "1G" gibi (UDP için rate)
        extra: Optional[str] = None,          # ek özel argümanlar
    ) -> str:
        ...

    @abstractmethod
    def setPing(
        self,
        *,
        target: str,                          # zorunlu
        count: Optional[int] = None,          # adet
        interval: Optional[float] = None,     # saniye (Linux destekler)
        timeout: Optional[int] = None,        # saniye (Win: ms'e çevrilir)
        size: Optional[int] = None,           # paket boyutu
        ipv6: bool = False,                   # IPv6 ping
        do_not_fragment: bool = False,        # DF bit (Linux: -M do; Win: -f)
        ttl: Optional[int] = None,            # Time To Live
        extra: Optional[str] = None,          # ek özel argümanlar
    ) -> str:
        ...


# -------------------------- Linux Strategy -----------------------------------
class Linux(Strategy):
    def setIperf3(
        self,
        *,
        role: str = "client",
        server: Optional[str] = None,
        port: Optional[int] = 5201,
        duration: Optional[int] = None,
        parallel: Optional[int] = None,
        reverse: bool = False,
        udp: bool = False,
        bandwidth: Optional[str] = None,
        extra: Optional[str] = None,
    ) -> str:
        parts = ["iperf3"]
        if role == "server":
            parts.append("-s")
            if port: parts += ["-p", str(port)]
        else:  # client
            if not server:
                raise ValueError("Linux iperf3 client için 'server' zorunlu.")
            parts += ["-c", shlex.quote(server)]
            if port: parts += ["-p", str(port)]
            if duration: parts += ["-t", str(duration)]
            if parallel: parts += ["-P", str(parallel)]
            if reverse: parts.append("-R")
            if udp:
                parts.append("-u")
                if bandwidth:
                    parts += ["-b", shlex.quote(bandwidth)]
            elif bandwidth:
                # TCP'de -b yok; yine de kullanıcı verdiyse yok sayıyoruz.
                pass
        if extra:
            parts.append(extra)  # kullanıcı bilinçli ekliyorsa olduğu gibi ekle
        return " ".join(parts)

    def setPing(
        self,
        *,
        target: str,
        count: Optional[int] = None,
        interval: Optional[float] = None,
        timeout: Optional[int] = None,
        size: Optional[int] = None,
        ipv6: bool = False,
        do_not_fragment: bool = False,
        ttl: Optional[int] = None,
        extra: Optional[str] = None,
    ) -> str:
        cmd = ["ping6" if ipv6 else "ping"]
        if count: cmd += ["-c", str(count)]
        if interval: cmd += ["-i", str(interval)]
        if timeout: cmd += ["-w", str(timeout)]
        if size: cmd += ["-s", str(size)]
        if do_not_fragment: cmd += ["-M", "do"]
        if ttl: cmd += ["-t", str(ttl)]
        if extra: cmd.append(extra)
        cmd.append(shlex.quote(target))
        return " ".join(cmd)


# ------------------------- Windows Strategy ----------------------------------
class Windows(Strategy):
    def setIperf3(
        self,
        *,
        role: str = "client",
        server: Optional[str] = None,
        port: Optional[int] = 5201,
        duration: Optional[int] = None,
        parallel: Optional[int] = None,
        reverse: bool = False,
        udp: bool = False,
        bandwidth: Optional[str] = None,
        extra: Optional[str] = None,
    ) -> str:
        # iperf3 parametreleri Windows'ta da aynıdır.
        parts = ["iperf3"]
        if role == "server":
            parts.append("-s")
            if port: parts += ["-p", str(port)]
        else:
            if not server:
                raise ValueError("Windows iperf3 client için 'server' zorunlu.")
            parts += ["-c", f'"{server}"']
            if port: parts += ["-p", str(port)]
            if duration: parts += ["-t", str(duration)]
            if parallel: parts += ["-P", str(parallel)]
            if reverse: parts.append("-R")
            if udp:
                parts.append("-u")
                if bandwidth:
                    parts += ["-b", f'"{bandwidth}"']
        if extra:
            parts.append(extra)
        return " ".join(parts)

    def setPing(
        self,
        *,
        target: str,
        count: Optional[int] = None,
        interval: Optional[float] = None,  # Windows ping'te yok, yok sayacağız
        timeout: Optional[int] = None,     # ms cinsinden ister; saniyeyi ms'e çeviriyoruz
        size: Optional[int] = None,
        ipv6: bool = False,
        do_not_fragment: bool = False,
        ttl: Optional[int] = None,
        extra: Optional[str] = None,
    ) -> str:
        cmd = ["ping"]
        cmd.append("-6" if ipv6 else "-4")  # IPv6/IPv4 zorlamak istersen
        if count: cmd += ["-n", str(count)]
        if timeout is not None:
            # Windows 'ping -w' ms bekleme alır; kullanıcı saniye verdiyse çevir
            ms = timeout if timeout > 50 else int(timeout * 1000)
            cmd += ["-w", str(ms)]
        if size: cmd += ["-l", str(size)]
        if do_not_fragment: cmd.append("-f")
        if ttl: cmd += ["-i", str(ttl)]
        if extra: cmd.append(extra)
        cmd.append(f'"{target}"')
        return " ".join(cmd)


if __name__ == "__main__":
    # Küçük örnekler:
    exe = CommandExecutor(Linux())
    print(exe.comand_Iperf3(role="client", server="10.0.0.1", duration=10, parallel=2))
    print(exe.command_Ping(target="8.8.8.8", count=4, interval=0.2))
    exe.strategy = Windows()
    print(exe.command_Ping(target="8.8.8.8", count=4, timeout=2))
