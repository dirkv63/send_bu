import logging
import os
import re
import sys
from ftplib import FTP


class ftp_handler:

    """
    This class consolidates the FTP functions. On initialization the FTP Connection object is created
    in the directory that the configuration file specifies.
    Note that there is no FTP close for now. Not sure if it is required?
    """

    def __init__(self, config_hdl):
        self.ftp_hdl = self._ftp_connection(config_hdl)

    @staticmethod
    def _ftp_connection(config_hdl):
        """
        This procedure establishes an FTP connection to the FTP Server. The FTP connection points to the directory
        specified in the config file.

        :return: ftp object.
        """
        # TODO proper error handling: if FTP connection fails, FTP is NoType at this moment and will fail at ftp.close()
        log_msg = "Trying to establish FTP Connection"
        logging.debug(log_msg)
        host = config_hdl['FTPServer']['host']
        user = config_hdl['FTPServer']['user']
        passwd = config_hdl['FTPServer']['passwd']
        ftp = FTP()
        # ftp.set_pasv(False)
        # First connect to the FTP Server
        try:
            log_msg = "Connect to FTP Server"
            logging.debug(log_msg)
            ftp.connect(host=host, timeout=10)
        except:
            ec = sys.exc_info()[0]
            e = sys.exc_info()[1]
            log_msg = "Error during connect to FTP Server: %s %s"
            logging.critical(log_msg, e, ec)
            sys.exit('ftp_connection failed')
        # Then login to FTP Server
        try:
            log_msg = "Login at FTP Server"
            logging.debug(log_msg)
            ftp.login(user=user, passwd=passwd)
        except:
            ec = sys.exc_info()[0]
            e = sys.exc_info()[1]
            log_msg = "Error during FTP login: %s %s \n\n"
            logging.critical(log_msg, e, ec)
            sys.exit()
        # Connected to FTP Server, now change to directory
        ftpdir = config_hdl['FTPServer']['dir']
        try:
            ftp.cwd(ftpdir)
        except:
            ec = sys.exc_info()[0]
            e = sys.exc_info()[1]
            log_msg = "Error during cwd to FTP Server: %s %s"
            logging.critical(log_msg, e, ec)
            sys.exit('ftp_cwd failed')
        return ftp

    def load_file(self, file=None, fn=None):
        """
        Load file on FTP Server. If file exists already, then overwrite.

        :param file: Filename (including path) of the file to be loaded.

        :param fn: Name of the file on the remote server. If not specified, then same name as on the sending server.

        :return: Result of the FTP command.
        """
        log_msg = "Moving file %s to FTP Server"
        logging.debug(log_msg, file)
        # Get Filename from file pointer
        (filepath, filename) = os.path.split(file)
        # Load the File
        try:
            f = open(file, mode='rb')
        except:
            e = sys.exc_info()[1]
            log_msg = "Error to open file {e}".format(e=e)
            logging.critical(log_msg)
            return log_msg
        if fn:
            stor_cmd = 'STOR ' + fn
        else:
            fn = filename
            stor_cmd = 'STOR' + fn
        try:
            self.ftp_hdl.storbinary(stor_cmd, f)
        except:
            e = sys.exc_info()[1]
            log_msg = "Error loading file: {e}".format(e=e)
            logging.critical(log_msg)
            return log_msg
        log_msg = "Looks like file {f} is moved to FTP Server.".format(f=file)
        logging.debug(log_msg)
        rem_size = self.ftp_hdl.size(fn)
        local_size = os.path.getsize(file)
        log_msg += "\nRemote size: {r:,} bytes, local size: {l:,} bytes.".format(r=rem_size, l=local_size)
        f.close()
        return log_msg
