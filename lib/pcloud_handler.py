import logging
import os
import requests
import sys
from ftplib import FTP


class PcloudHandler:

    """
    This class consolidates the pcloud functionality. On initialization a connection to pcloud account is set and
    the folder ID for the requested backup folder is set. The backup folder must be child of the root folder, not
    grandchild or later.
    List method allows to list all files in the specified folder. Load method will load the file to the backup directory
    on pcloud. Logout method will close the connection.
    """

    def __init__(self, config_hdl):
        """
        On initialization a connection to pcloud account is done, including obtaining the folderid for the backup
        folder.
        :param config_hdl:
        """
        user = config_hdl["Pcloud"]["user"]
        passwd = config_hdl["Pcloud"]["passwd"]
        params = dict(username=user, password=passwd, getauth=1, path="/")
        self.url_base = config_hdl["Pcloud"]["home"]
        method = "listfolder"
        url = self.url_base + method
        r = requests.get(url, params=params)
        if r.status_code != 200:
            msg = "Could not connect to pcloud. Status: {s}, reason: {reason}.".format(s=r.status_code, reason=r.reason)
            logging.critical(msg)
            raise SystemExit()
        # Status Code OK, so successful login
        res = r.json()
        self.auth = res["auth"]
        folder = res["metadata"]["content"]
        for item in folder:
            if item["isfolder"]:
                obj = "Folder"
            else:
                obj = "File"
            print("Found {obj}: {name}".format(obj=obj, name=item["name"]))

    def logout(self):
        method = "logout"
        url = self.url_base + method
        params =