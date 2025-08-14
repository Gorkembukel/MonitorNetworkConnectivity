import paramiko
import time
import re
import sys

HOST = "127.0.0.1"
PORT = 22
USER = "gork"
PASS = "657665"

SENTINEL = "__CMD_DONE__"
PROMPT = "__P__ "

def read_until(channel, pattern, timeout=10):
    end = time.time() + timeout
    buf = ""
    regex = re.compile(re.escape(pattern)) if isinstance(pattern, str) else pattern
    while time.time() < end:
        if channel.recv_ready():
            chunk = channel.recv(4096).decode(errors="ignore")
            buf += chunk
            if regex.search(buf):
                return buf
        else:
            time.sleep(0.03)
    return buf

def flush_all(channel, delay=0.2):
    time.sleep(delay)
    out = ""
    while channel.recv_ready():
        out += channel.recv(4096).decode(errors="ignore")
    return out

def clean_output(raw, cmd):
    raw = raw.replace(SENTINEL, "")
    lines = raw.splitlines()
    if lines and lines[0].strip() == cmd.strip():
        lines = lines[1:]
    return "\n".join(lines).strip()

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, PORT, USER, PASS)

    chan = client.invoke_shell()
    chan.settimeout(0.0)

    # Banner/MOTD temizle
    flush_all(chan, 0.3)

    # Stabil prompt
    chan.send(f'export PS1="{PROMPT}"\n')
    read_until(chan, PROMPT, timeout=5)

    print(f"{USER}@{HOST} ile bağlantı kuruldu. Çıkmak için 'exit' yaz.")
    try:
        while True:
            cmd = input(f"{USER}@remote$ ").strip()
            if cmd.lower() in ("exit", "quit"):
                print("Bağlantı kapatılıyor...")
                break
            if not cmd:
                continue

            # --- AKIŞ MODU ---
            if cmd.startswith("stream "):
                real_cmd = cmd[len("stream "):].strip()
                if not real_cmd:
                    print("Kullanım: stream <komut>")
                    continue

                chan.send(real_cmd + "\n")
                print("[Akış başladı; durdurmak için Ctrl+C]")
                try:
                    while True:
                        if chan.recv_ready():
                            sys.stdout.write(chan.recv(4096).decode(errors="ignore"))
                            sys.stdout.flush()
                        else:
                            time.sleep(0.05)
                except KeyboardInterrupt:
                    # Uzağa Ctrl+C (SIGINT) gönder
                    chan.send('\x03')
                    # Prompt geri gelene kadar biraz bekle + temizle
                    read_until(chan, PROMPT, timeout=10)
                    flush_all(chan, 0.1)
                    print("\n[Akış durduruldu]")
                continue

            # --- NORMAL MOD (sentinel) ---
            chan.send(cmd + f"; echo {SENTINEL}\n")
            raw = read_until(chan, SENTINEL, timeout=60)
            out = clean_output(raw, cmd)
            if out:
                print(out)

    finally:
        client.close()

if __name__ == "__main__":
    main()
