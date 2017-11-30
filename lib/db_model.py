"""
This is the data model.
"""

from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class FileHash(Base):
    """
    Table containing the file hashes.
    """
    __tablename__ = "filehash"
    file_id = Column(Text, primary_key=True)
    fh = Column(Text, nullable=False)
    created = Column(Integer, nullable=False)
    modified = Column(Integer, nullable=False)

    def __repr__(self):
        return "<File: {fid} - hash: {h}>".format(fid=self.file_id, h=self.fh)
