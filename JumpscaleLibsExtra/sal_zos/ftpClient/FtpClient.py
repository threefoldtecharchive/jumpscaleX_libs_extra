from ftplib import FTP
from io import BytesIO
from urllib.parse import urlparse


class FtpClient:
    def __init__(self, url):
        self.parsed_url = urlparse(url)

    def upload(self, content, filename):
        with FTP() as ftp:

            port = self.parsed_url.port or 21
            ftp.connect(self.parsed_url.hostname, port=port)
            ftp.login(user=self.parsed_url.username, passwd=self.parsed_url.password)
            if self.parsed_url.path:
                ftp.cwd(self.parsed_url.path)
            bytes = BytesIO(content)
            ftp.storbinary("STOR " + filename, bytes)

    def download(self, filename=None):
        filename = filename or self.parsed_url.path
        with FTP() as ftp:
            port = self.parsed_url.port or 21
            ftp.connect(self.parsed_url.hostname, port=port)
            ftp.login(user=self.parsed_url.username, passwd=self.parsed_url.password)
            buff = BytesIO()
            ftp.retrbinary("RETR " + filename, buff.write)
            return buff.getvalue().decode()
