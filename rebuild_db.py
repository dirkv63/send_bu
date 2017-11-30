"""
This procedure will rebuild the sqlite sendmail database
"""

import logging
from lib import my_env
from lib import info_layer

cfg = my_env.init_env("sendmail", __file__)
logging.info("Start application")
sm = info_layer.DirectConn(cfg)
sm.rebuild()
logging.info("sqlite sendmail rebuild")
logging.info("End application")
