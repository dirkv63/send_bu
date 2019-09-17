import hashlib
import lib.my_env as my_env
import logging
import os
import sqlite3
import time
from lib.db_model import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound


class SqlAlConn:
    """
    This class creates an sqlalchemy connection and has functions to handle the data.
    """

    def __init__(self, config, echo=False):
        """
        SqlAlchemy Session

        :param config:

        :param echo:
        """
        self.sess = init_session(config, echo)

    def file_remove(self, file_id):
        """
        This method will remove the file from the database. This is required when a file backup didn't succeed. By
        removing the file from the database, the file will be flagged for load on the next run.

        :param file_id: Unique identifier for the file, use filename.

        :return:
        """
        self.sess.query(FileHash).filter_by(file_id=file_id).delete()
        self.sess.commit()
        return

    def file_update(self, file_id, fc):
        """
        This method will check if the file is updated since last run.

        :param file_id: Unique identifier for the file, use filename.
        :param fc: Contents (slurp) of the file.
        :return: True if the file was updated, False if there is no change.
        """
        # Get the hash for the file
        m = hashlib.sha256()
        m.update(fc)
        fh = m.hexdigest()
        # Check if file is changed since last run
        try:
            fr = self.sess.query(FileHash).filter_by(file_id=file_id).one()
        except NoResultFound:
            # New file, add to database
            frec = FileHash(
                file_id=file_id,
                fh=fh,
                created=int(time.time()),
                modified=int(time.time())
            )
            self.sess.add(frec)
            self.sess.commit()
            return True
        # Existing file, check if there was an update
        if fr.fh == fh:
            # Same checksum, no need to update
            return False
        else:
            fr.fh = fh
            fr.modified = int(time.time())
            self.sess.commit()
            return True


class DirectConn:
    """
    This class will set up a direct connection to the database. It allows to reset the database,
    in which case the database will be dropped and recreated, including all tables.
    """

    def __init__(self, config):
        """
        To drop a database in sqlite3, you need to delete the file.
        """
        if my_env.is_prod(config):
            env = 'Prod'
        else:
            env = 'Dev'
        self.db = config[env]['db']
        self.dbConn = ""
        self.cur = ""

    def _connect2db(self):
        """
        Internal method to create a database connection and a cursor. This method is called during object
        initialization.
        Note that sqlite connection object does not test the Database connection. If database does not exist, this
        method will not fail. This is expected behaviour, since it will be called to create databases as well.

        :return: Database handle and cursor for the database.
        """
        logging.debug("Creating Datastore object and cursor")
        db_conn = sqlite3.connect(self.db)
        # db_conn.row_factory = sqlite3.Row
        logging.debug("Datastore object and cursor are created")
        return db_conn, db_conn.cursor()

    def rebuild(self):
        # A drop for sqlite is a remove of the file
        try:
            os.remove(self.db)
        except FileNotFoundError:
            # If the file is not there, then do not delete it.
            pass
        # Reconnect to the Database
        self.dbConn, self.cur = self._connect2db()
        # Use SQLAlchemy connection to build the database
        conn_string = "sqlite:///{db}".format(db=self.db)
        engine = set_engine(conn_string=conn_string)
        Base.metadata.create_all(engine)


def init_session(config, echo=False):
    """
    This function configures the connection to the database and returns the session object.

    :param config:

    :param echo: True / False, depending if echo is required. Default: False

    :return: session object.
    """
    if my_env.is_prod(config):
        env = 'Prod'
    else:
        env = 'Dev'
    db = config[env]['db']
    conn_string = "sqlite:///{db}".format(db=db)
    engine = set_engine(conn_string, echo)
    session = set_session4engine(engine)
    return session


def set_engine(conn_string, echo=False):
    engine = create_engine(conn_string, echo=echo)
    return engine


def set_session4engine(engine):
    session_class = sessionmaker(bind=engine)
    session = session_class()
    return session
