import logging
import os
import requests


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
        self.session = requests.Session()
        r = self.session.get(url, params=params)
        if r.status_code != 200:
            msg = "Could not connect to pcloud. Status: {s}, reason: {reason}.".format(s=r.status_code, reason=r.reason)
            logging.critical(msg)
            raise SystemExit(msg)
        # Status Code OK, so successful login
        res = r.json()
        self.auth = res["auth"]
        items = res["metadata"]["contents"]
        bu_dir = config_hdl["Pcloud"]["dir"]
        for item in items:
            if item["isfolder"] and item["name"] == bu_dir:
                self.folderid = item["folderid"]
                break
        else:
            msg = "Could not find Backup directory {bu_dir}".format(bu_dir=bu_dir)
            logging.critical(msg)
            raise SystemExit(msg)

    def upload(self, filepath):
        """
        This method will upload a file. Note that the Filename key value in the requests post array is of no value, the
        filename is guessed from the fileobject body.
        :param filepath: Full path for the file
        :return:
        """
        print("Filepath: {fp}".format(fp=filepath))
        params = dict(
            auth=self.auth,
            folderid=self.folderid
        )
        method = "uploadfile"
        url = self.url_base + method
        with open(filepath, 'rb') as body:
            files = {"dummyfilename": body}
            r = self.session.post(url, files=files, data=params)
            if r.status_code != 200:
                msg = "Upload file {fp} not successful. Status: {s}, reason: {reason}.".format(s=r.status_code,
                                                                                               reason=r.reason,
                                                                                               fp=filepath)
                logging.error(msg)
            else:
                res = r.json()
                flinfo = res["metadata"][0]
                rem_size = flinfo["size"]
                local_size = os.path.getsize(filepath)
                if rem_size == local_size:
                    msg = "Upload {fp} successful, {size:,} bytes transferred".format(size=flinfo["size"],
                                                                                      fp=flinfo["name"])
                    logging.info(msg)
                else:
                    msg = "Upload {fp} not complete, " \
                          "{lcl:,} bytes required, {rem:,} bytes received.".format(fp=filepath, lcl=local_size,
                                                                                   rem=rem_size)
                    logging.error(msg)
        return msg

    def logout(self):
        method = "logout"
        url = self.url_base + method
        params = dict(auth=self.auth)
        r = self.session.get(url, params=params)
        if r.status_code != 200:
            msg = "Could not logout from pcloud. Status: {s}, reason: {rsn}.".format(s=r.status_code, rsn=r.reason)
            logging.error(msg)
        else:
            res = r.json()
            if res["auth_deleted"]:
                msg = "Logout as required"
            else:
                msg = "Logout not successful, status code: {status}".format(status=r.status_code)
            logging.info(msg)
