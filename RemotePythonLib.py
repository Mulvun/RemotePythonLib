#Coded by Mulvun, greetz to 1llM1ND3D
from getpass import getpass
from typing import List

from paramiko import SSHClient, AutoAddPolicy
from paramiko.hostkeys import HostKeys


class _RePyError(Exception):
    pass


class _RePyClient(object):
    def __init__(self, user, host, pswd, port, sudo, sudopass):
        self.user: str = user
        self.host: str = host
        self.pswd: str = pswd
        self.sudo: bool = sudo
        self.port: int = port
        self.sudopass: str = sudopass
        self.pyver: str = ''

    def __repr__(self):
        return str({'user': self.user, 'host': self.host, 'pswd': self.pswd, 'port': self.port, 'sudo': self.sudo,
                    'python_version': self.pyver})

    def __str__(self):
        return f'Client(user:{self.user}, host:{self.host}, pswd:{self.pswd}, port:{self.port}, sudo:{self.sudo}, python_version:{self.pyver})'


class SSH(_RePyClient, _RePyError):
    def __init__(self, user, host, pswd='', port=22, sudo=False, sudopass=''):
        super().__init__(user, host, pswd, port, sudo, sudopass)
        self._ssh = SSHClient()
        self._ssh.set_missing_host_key_policy(AutoAddPolicy)
        self._ssh.load_system_host_keys()

        if not HostKeys().lookup(self.host):
            if not self.pswd:
                getpass(f'No key found for {self.user}@{self.host}, please enter password: [WILL NOT ECHO]')
            self.ssh_client = self._ssh.connect(hostname=self.host, username=self.user, password=self.pswd,
                                                port=self.port)
        else:
            self.ssh_client = self._ssh.connect(hostname=self.host, username=self.user, port=self.port)

        self.pyver = self.execute('python --version').strip()
        if not self.pyver:
            raise _RePyError('Python is not accessible on the remote host. Check if it is installed.')

    def pyxecute(self, commands: List[str] or str) -> str:
        if isinstance(commands, list):
            for file in commands:
                command = self.sudoer(f'python <<EOF\n \n{open(file).read()} \nEOF')
                return self.pseudo(command)
        elif isinstance(commands, str):
            command = self.sudoer(f'python <<EOF\n \n{commands} \nEOF')
            return self.pseudo(command)
        else:
            raise _RePyError('SSH.pyxecute only accepts a list of files to read and execute or a single python '
                             'command string.')

    def execute(self, files: List[str] or str) -> str:
        if isinstance(files, list):
            for file in files:
                command = self.sudoer(f'{open(file).read()}')
                return self.pseudo(command)
        elif isinstance(files, str):
            command = self.sudoer(files)
            return self.pseudo(command)
        else:
            raise _RePyError('SSH.execute only accepts a list of files to read and execute ore a single shell command '
                             'string')

    def sudoer(self, text: str) -> str:
        if self.sudo:
            return f"sudo -S -p '' {text}"
        else:
            return text

    def pseudo(self, command):
        stdin, stdout, stderr = self._ssh.exec_command(command=command, get_pty=True)
        if self.sudo:
            stdin.write(self.sudopass + '\n')
            stdin.flush()
        stdin.close()
        return stdout.read().decode('utf8').replace(self.sudopass, '')


class SFTP(_RePyClient, _RePyError):
    def __init__(self, user, host, pswd='', port=22, sudo=False, sudopass=''):
        super().__init__(user, host, pswd, port, sudo, sudopass)
        self._ssh = SSHClient()
        self._ssh.set_missing_host_key_policy(AutoAddPolicy)
        self._ssh.load_system_host_keys()

        if not HostKeys().lookup(self.host):
            if not self.pswd:
                getpass(f'No key found for {self.user}@{self.host}, please enter password: [WILL NOT ECHO]')
            self.ssh_client = self._ssh.connect(hostname=self.host, username=self.user, password=self.pswd,
                                                port=self.port)
        else:
            self.ssh_client = self._ssh.connect(hostname=self.host, username=self.user, port=self.port)

        self._sftp = self._ssh.open_sftp()

    def get_file(self, rem_path, lcl_path):
        self._sftp.get(rem_path, lcl_path)

    def put_file(self, lcl_path, rem_path):
        self._sftp.put(lcl_path, rem_path)