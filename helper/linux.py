from paramiko import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import SSHException
from paramiko.util import log_to_file
from typing import Dict, Union, List
from pathlib import Path
import os
from types import MappingProxyType
import sys

# The progress bar for download and upload files.
from helper.progress_bar import progress_bar

# Consolidate Errors
CONN_EXCEPTION = SSHException, TypeError, PermissionError

# Home directory for OS, works on Linux and Windows, not sure about others.
HOME_PATH = str(Path.home())

# https://docs.python.org/2/library/logging.html#levels
LOG_LEVEL = MappingProxyType(
    {
        "NOTSET": 0,
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }
)


def get_file_hash(base_path: str = None, filename: str = None):
    """
    https://nitratine.net/blog/post/how-to-hash-files-in-python/
    The concept, read the target file block by block, each block size is 65535 bytes.
    On each block calculate the hash until the EOF.
    Then write the entire digest back to a file.
    I have tested between 8KB of python script file and 600MB of centos iso file and both results are good, also
    on centos i have use the sha256sum to calculate the digests which are the same with the hash files uploaded.
    :param filename:
        name of the file
    :param base_path:
        base directory of the file, I use this because I need the base_path to write the hash to file.
    :return:
    """
    file_path = os.path.join(base_path, filename)

    # normally loaded at first, but i prefer the library to be loaded if in use.
    import hashlib

    BLOCK_SIZE = 65535
    digest = hashlib.sha256()
    with open(file_path, "rb") as file:
        # read the first 65535 bytes from the file.
        file_blocks = file.read(BLOCK_SIZE)
        while len(file_blocks) > 0:
            digest.update(file_blocks)
            file_blocks = file.read(BLOCK_SIZE)
    with open(os.path.join(base_path, f"{filename}.sha256"), "w") as write_hash:
        write_hash.write(digest.hexdigest())
    return f"{filename}.sha256"


class LinuxSSH(SSHClient):
    """
    This is a sub class of SSHClient, this is to add on some methods while still having the functionalities of
    SSHClient.
    """
    def __init__(self, username: str = None,
                 password: str = None,
                 hostname: str = "127.0.0.1",
                 port: int = 22,
                 log_file: str = None,
                 level: int = None):
        super().__init__()
        if log_file is not None and level is not None:
            log_to_file(log_file, level=level)
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self._policy = AutoAddPolicy()  # modify the original default RejectPolicy()
        # Once an instance is created, a ssh session is attempted.
        try:
            self.connect(self.hostname, port=self.port, username=self.username, password=self.password)
        except CONN_EXCEPTION as CE:
            sys.stdout.write(f"Message: {str(CE)}")
            sys.exit(1)

    def get_project_dirs(self, dirname: str = "/var/lib/awx/projects") -> Union[Dict[str, str], Dict[str, List]]:
        """
        To get a list of directories under the Ansible AWX base project directory.
        :param dirname:
            Project base directory. Ansible searches the yaml file from base directory.
        :return:
            dictionary of response.
        """
        try:
            # exec_command throws up a tuple(stdin, stdout, stderr)
            stdin, stdout, _ = self.exec_command(f"sudo ls -lah {dirname}", get_pty=True)
            stdin.write(self.password + "\n")
            stdin.flush()
            stdout_results = stdout.read().decode("utf-8")
            pbdirs = list()
            for row in stdout_results.splitlines()[3:]:  # Not interested in password, sudo prompt and total 0
                # if "d" is found in the row
                if "d" in row.split()[0]:
                    pbdirs.append(row.split()[-1])  # the directory name is in the last index of the row.
            return {
                "status": "success",
                "playbook_dirs": pbdirs[2:] if len(pbdirs) > 2 else []  # not interested in . and ..
            }
        except CONN_EXCEPTION as CE:
            return {
                "status": "failed",
                "message": str(CE)
            }

    def create_project_dir(self, base_path: str = "/var/lib/awx/projects", dirname: str = None):
        """
        Create project directory.
        :param base_path:
            Project base path
        :param dirname:
            New project directory, this directory is attached to the manual project of Ansible AWX
        :return:
        """
        response = self.get_project_dirs(dirname=base_path)
        if response["status"] == "success":
            # a list of directory names where the playbook is stored.
            pbdirs = response["playbook_dirs"]
        else:
            return response
        if dirname not in pbdirs or pbdirs == list():
            # create the directory if not exists.
            commands = [f"sudo mkdir {base_path}/{dirname}",
                        f"sudo chown -R awx:awx {base_path}/{dirname}"]
            try:
                for command in commands:
                    stdin, stdout, _ = self.exec_command(command, get_pty=True)
                    # sudo password
                    stdin.write(self.password + "\n")
                    stdin.flush()
                    stdout.read().decode("utf-8")
            except CONN_EXCEPTION as CE:
                return {
                    "status": "failed",
                    "message": str(CE)
                }
        else:
            return {
                "status": "failed",
                "message": f"{dirname} exists."
            }

    def remove_project_dir(self, base_path: str = "/var/lib/awx/projects", dirname: str = None):
        """
        This is for project directory removal, project directory is required to be attached to Ansible AWX
        project.
        :param base_path:
            Project base path.
        :param dirname:
            directory name under the base path.
        :return:
        """
        if dirname is None:
            return {
                "status": "failed",
                "message": "You have forgotten to provide the project dir name you want to remove."
            }
        response = self.get_project_dirs(dirname=base_path)
        if response["status"] == "success":
            # list of directory names under project base directory.
            pbdirs = response["playbook_dirs"]
        else:
            return response
        if dirname in pbdirs:
            # if the requested directory for removal exists, prepare the rm command.
            command = f"sudo rm -rf {base_path}/{dirname}"
            try:
                stdin, stdout, stderr = self.exec_command(command, get_pty=True)
                # sudo password
                stdin.write(self.password + "\n")
                stdin.flush()
            except CONN_EXCEPTION as CE:
                return {
                    "status": "failed",
                    "message": str(CE)
                }
        else:
            return {
                "status": "failed",
                "message": f"{dirname} does not exists."
            }

    def download(self, src_abs_path: str = None,
                 dst_path: str = HOME_PATH,
                 dst_filename: str = None):
        """
        This method does sftp download, SSHClient can easily create a SFTPClient object by calling
        self.open_sftp(), once a SFTPClient instance is created we can use the get method to download.
        :param src_abs_path:
            Absolute path of the file you wish to download from the remote CentOS server.
        :param dst_path:
            Local path of your computer where this script is executed.
        :param dst_filename:
            Filename to be created with the download object, this is optional, you can put in the full path
            with the file name in local_base_path.
        :return:
        """
        if dst_filename is not None:
            local_path = os.path.join(dst_path, dst_filename)
        else:
            local_path = dst_path
        with self.open_sftp() as sftp:
            """
            The sftp open and close session is handled here, so user does not need to close the sftp session.
            The purpose is to have a more straightforward way to download/upload files to target server.
            """
            # B is byte, b is bit. Miniters will have a better looking bar.
            # ascii=True will give # as the bar.
            callback, pbar = progress_bar(unit="B", unit_scale=True, miniters=1)
            try:
                sftp.get(src_abs_path, local_path, callback=callback)
            except CONN_EXCEPTION as CE:
                return {
                    "status": "failed",
                    "message": str(CE)
                }

    def upload(self, src_path: str = HOME_PATH,
               src_filename: str = None,
               dst_abs_path: str = None):
        """
        This method uploads the file from your computer to remote server.
        :param src_filename:
            src_filename, this is for used with get_file_hash.
        :param src_path:
            the base path of where the src_filename can be found.
        :param dst_abs_path:
            The absolute path the file will be uploaded. os.path.join works properly in source, if the remote is
            a different OS the path will be wrong.
        :return:
        """
        if src_filename is not None:
            local_path = os.path.join(src_path, src_filename)
        else:
            local_path = src_path
        remote_path = dst_abs_path
        digest_filename = get_file_hash(base_path=src_path, filename=src_filename)
        digest_abs_path = os.path.join(src_path, digest_filename)
        with self.open_sftp() as sftp:
            """
            The sftp open and close session is handled here, so user does not need to close the sftp session.
            The purpose is to have a more straightforward way to download/upload files to target server.
            """
            # b is bit, B is byte. If ascii=True, # will be used for progress bar.
            callback, pbar = progress_bar(unit="B", unit_scale=True, miniters=1)
            try:
                sftp.put(local_path, remote_path, callback=callback)
                # The session to remote_path is still on, hence only target filename is required.
                sftp.put(digest_abs_path, digest_filename, callback=callback)
            except CONN_EXCEPTION as CE:
                return {
                    "status": "failed",
                    "message": str(CE)
                }
