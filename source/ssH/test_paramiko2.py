import paramiko
import threading
import time

hostname = "127.0.0.1"
port = 22
username = "gork"
password = "657665"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)

def _stream_channel(stdout, stderr, tag: str):
    ch = stdout.channel
    ch.settimeout(0.0)  # non-blocking
    try:
        while True:
            # STDOUT
            if ch.recv_ready():
                data = ch.recv(4096).decode(errors="replace")
                if data:
                    print(f"[{tag}] {data}", end="")
            # STDERR
            if ch.recv_stderr_ready():
                data_err = ch.recv_stderr(4096).decode(errors="replace")
                if data_err:
                    print(f"[{tag} ERR] {data_err}", end="")

            # İş bitti mi?
            if ch.exit_status_ready():
                # Kalan buffer'ı da boşalt
                while ch.recv_ready():
                    print(f"[{tag}] {ch.recv(4096).decode(errors='replace')}", end="")
                while ch.recv_stderr_ready():
                    print(f"[{tag} ERR] {ch.recv_stderr(4096).decode(errors='replace')}", end="")
                break

            time.sleep(0.05)
    finally:
        # channel stdout/stderr kapanınca otomatik kapanır; ekstra temizlik gerekmez
        pass

def add_command_async(cmd: str, tag: str, get_pty: bool = True):
    """Her çağrıda yeni channel açar ve çıktıyı ayrı thread'de tüketir."""
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=get_pty)
    t = threading.Thread(target=_stream_channel, args=(stdout, stderr, tag), daemon=True)
    t.start()
    return t, stdout.channel  # istersen channel id: stdout.channel.get_id()

# Örnek kullanım:

t2, ch2 = add_command_async("iperf3 -s", tag="iperf")  # uzun süreli
for x in range(20):
    t1, ch1 = add_command_async("ls -la", tag="ls")
    time.sleep(5)
# İstersen kısa ömürlüleri bekleyebilirsin
t1.join()  # ls biter
t2.join()  # iperf3 -s sunucusu normalde bitmez; manuel durdurman gerekir
