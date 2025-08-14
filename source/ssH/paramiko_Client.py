import paramiko

class Client:
    def __init__(self, hostname, username, password, port=22, osType:str = "linux"):
        self._osType = osType
        self.__hostname = hostname       # private attribute
        self.__username = username       # private attribute
        self.__password = password       # private attribute
        self.__port = port               # private attribute
        self.__client = None             # paramiko SSHClient nesnesi
        self.__sftp = None               # paramiko SFTPClient nesnesi

    # Private metot: bağlantı nesnesi oluşturur
    def __create_client(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())    
        return client

    # Public metot: SSH bağlantısı kurar
    def connect(self):
        if self.__client is None:
            self.__client = self.__create_client()
            self.__client.connect(
                hostname=self.__hostname,
                port=self.__port,
                username=self.__username,
                password=self.__password
            )
            print(f"[+] {self.__hostname} bağlantısı başarılı.")
        else:
            print("[!] Zaten bağlantı kurulmuş.")
    def greeting(self):
        if not self.__client:
            raise ConnectionError("Önce connect() metodunu çağırın.")

        # Linux testi
        try:
            _, stdout, _ = self.__client.exec_command("uname -s")
            out = stdout.read().decode(errors="replace").strip().lower()
            if "linux" in out:
                self._osType = "linux"
                return "linux"
        except Exception:
            pass

        # Windows testi
        try:
            _, stdout, _ = self.__client.exec_command("ver")
            out = stdout.read().decode(errors="replace").strip().lower()
            if "windows" in out or "microsoft" in out:
                self._osType = "windows"
                return "windows"
        except Exception:
            pass

        # İsteğe bağlı üçüncü deneme (bazı Windows ortamlarında daha kararlı)
        try:
            _, stdout, _ = self.__client.exec_command("wmic os get caption")
            out = stdout.read().decode(errors="replace").lower()
            if "windows" in out:
                self._osType = "windows"
                return "windows"
        except Exception:
            pass

        self._osType = "unknown"
        return "unknown"

    def get_osType(self):
        return self._osType
    # Public metot: SSH komutu çalıştırır
    def execute_command(self, command:str,get_pty =False,bufsize=-1,timeout=None, environment=None):# istenilen komutu girer ve çıktı kanalını döndürür, kanalı çeken yer okumak zorunda orası blocklanabilir
        if self.__client:
            stdin, stdout, stderr = self.__client.exec_command(command=command,get_pty= get_pty,bufsize = bufsize,timeout = timeout, environment= environment)
            return stdout, stderr
        else:
            raise ConnectionError("Önce connect() metodunu çağırın.")

    # Public metot: SFTP bağlantısı başlatır. Dosya aktarımı için
    def start_sftp(self):
        if self.__client:
            self.__sftp = self.__client.open_sftp()
            print("[+] SFTP bağlantısı başlatıldı.")
        else:
            raise ConnectionError("SSH bağlantısı kurulmadan SFTP başlatılamaz.")

    # Public metot: Dosya yükleme
    def upload_file(self, local_path, remote_path):
        if self.__sftp:
            self.__sftp.put(local_path, remote_path)
            print(f"[+] {local_path} -> {remote_path} yüklendi.")
        else:
            raise ConnectionError("SFTP bağlantısı yok.")

    # Public metot: Dosya indirme
    def download_file(self, remote_path, local_path):
        if self.__sftp:
            self.__sftp.get(remote_path, local_path)
            print(f"[+] {remote_path} -> {local_path} indirildi.")
        else:
            raise ConnectionError("SFTP bağlantısı yok.")

    #bağlantı var mı?
    def is_connect(self):
        if self.__client:
            return True
        else:
            return False
    # Public metot: Bağlantıyı kapatma
    def close(self):
        if self.__sftp:
            self.__sftp.close()
        if self.__client:
            self.__client.close()
        self.__client = None
        self.__sftp = None
        print("[+] Bağlantı kapatıldı.")
