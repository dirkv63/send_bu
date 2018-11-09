import logging
from lib import my_env
from lib import pcloud_handler

cfg = my_env.init_env("sendmail", __file__)
logging.info("Start application")
pc = pcloud_handler.PcloudHandler(cfg)
pc.logout()
logging.info("End application")
