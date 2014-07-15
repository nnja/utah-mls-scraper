import re
import csv
import json
import os

from sqlalchemy import (Column, Integer, DateTime, Date, Boolean,
                        String, Numeric, ForeignKey, or_, create_engine)
from sqlalchemy.orm import validates, relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError


engine = create_engine('sqlite:///mls.sql')
Session = sessionmaker(bind=engine)
Base = declarative_base()
session = Session()

FILENAME = 'export.csv'


class ReprMixin(object):
    """Hooks into SQLAlchemy's magic to make :meth:`__repr__`s.
    Source from: http://innuendopoly.org/arch/sqlalchemy-init-repr

    Any class that uses this mixin will have reprs in this format:
    Class(<col name>=<col value>,..)
    For all columns
    """

    def __repr__(self):
        def reprs():
            for col in self.__table__.c:
                yield col.name, repr(getattr(self, col.name))

        def format(seq):
            for key, value in seq:
                yield '%s=%s' % (key, value)

        args = '(%s)' % ', '.join(format(reprs()))
        classy = type(self).__name__
        return classy + args


class Listing(ReprMixin, Base):
    __tablename__ = 'listing'
    id = Column(Integer, primary_key=True)
    # query_id = Column(Integer, ForeignKey('query.id'))
    zip_code = Column(Integer, nullable=False)
    mls = Column(Integer, unique=True, nullable=False)
    url = Column(String, nullable=False)
    address = Column(String)
    city = Column(String)
    price = Column(Numeric(precision=2, asdecimal=False), default=0.00)
    last_scraped = Column(DateTime)
    is_new = Column(Boolean)
    is_updated = Column(Boolean)
    county = Column(String)
    sub_div = Column(String)
    active = Column(Boolean, default=True)
    list_date = Column(Date)

    def save(self):
        session.add(self)
        session.commit()
        print 'SAVING: Listing with mls id %s' % self.mls

    @classmethod
    def get_listing(cls, mls):
        try:
            return session.query(cls).filter_by(mls=mls).one()
        except NoResultFound:
            return None

    @classmethod
    def get_last_mls(cls):
        return session.query(cls).order_by(cls.id.desc()).first().mls + 1


class ValidationException(Exception):
    """ An exception representing an invalid state. """
    pass


def init_db():
    from models import Base, engine
    Base.metadata.create_all(engine)


def export_json():
    row2dict = lambda r: {c.name: str(getattr(r, c.name))
                          for c in r.__table__.columns}
    listings = session.query(Listing).all()
    d = [row2dict(row) for row in listings]
    f = open('listings.json', 'w')
    print >> f, d
    f.close()


def file_is_empty(path):
    return os.stat(path).st_size==0


def export_csv(filename=FILENAME, initial_mls=Listing.get_last_mls()):
    listings_exist = session.query(Listing).all()

    if file_is_empty(FILENAME):
        outfile=open(filename, 'wb')
        outcsv = csv.writer(outfile)

        headers = Listing.__table__.columns.keys()
        outcsv.writerow(headers)

        records = session.query(Listing).all()
    else:
        outfile = open(filename, 'a')
        outcsv = csv.writer(outfile)
    
        records = session.query(Listing).filter(Listing.mls>initial_mls).all()

    [outcsv.writerow(
        [getattr(curr, column.name)
         for column in Listing.__mapper__.columns]) for curr in records]

    outfile.close()
    print 'file %s written successfully.' % filename
