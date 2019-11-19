import os, sys
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Representative(Base):
    __tablename__ = 'reps'

    dist =          Column(Integer, primary_key=True, nullable=False)
    last_name =     Column(String(500))
    first_name =    Column(String(500))
    sex =           Column(String(500))
    party =         Column(String(500))
    gov_bio =       Column(String(500))
    counties =      Column(String(500))
    rep_since =     Column(String(500))
    committees =    Column(String(500))
    dist_phone =    Column(String(500))
    dist_fax =      Column(String(500))
    cap_phone =     Column(String(500))
    cap_fax =       Column(String(500))
    dist_address =  Column(String(500))
    cap_address =   Column(String(500))
    pers_site =     Column(String(500))
    facebook =      Column(String(500))
    twitter =       Column(String(500))
    youtube =       Column(String(500))
    instagram =     Column(String(500))
    google_plus =   Column(String(500))
    linkedin =      Column(String(500))
    leadership =    Column(String(500))

class Senator(Base):
    __tablename__ = 'sens'

    dist =          Column(Integer, primary_key=True, nullable=False)
    last_name =     Column(String(500))
    first_name =    Column(String(500))
    sex =           Column(String(500))
    party =         Column(String(500))
    gov_bio =       Column(String(500))
    counties =      Column(String(500))
    sen_since =     Column(String(500))
    term_expires =  Column(String(500))
    committees =    Column(String(500))
    dist_phone =    Column(String(500))
    dist_fax =      Column(String(500))
    cap_phone =     Column(String(500))
    cap_fax =       Column(String(500))
    dist_address =  Column(String(500))
    cap_address =   Column(String(500))
    pers_site =     Column(String(500))
    facebook =      Column(String(500))
    twitter =       Column(String(500))
    youtube =       Column(String(500))
    instagram =     Column(String(500))
    google_plus =   Column(String(500))
    linkedin =      Column(String(500))
    leadership =    Column(String(500))

class HouseBills(Base):
    __tablename__ = 'housebills'

    search_id =     Column(String(500))
    bill_id =       Column(String(500), primary_key=True)
    title =         Column(String(500))
    summary =       Column(String(500))
    primesponsor =  Column(String(500))
    cosponsors =    Column(String(5000))
    passedhouse =   Column(String(500))
    passedsenate =  Column(String(500))
    enacted =       Column(String(500))
    lastaction =    Column(String(500))
    link =          Column(String(500))
    published =     Column(String(500))
    committees =    Column(String(500))

class SenateBills(Base):
    __tablename__ = 'senatebills'

    search_id =     Column(String(500))
    bill_id =       Column(String(500), primary_key=True)
    title =         Column(String(500))
    summary =       Column(String(500))
    primesponsor =  Column(String(500))
    cosponsors =    Column(String(5000))
    passedhouse =   Column(String(500))
    passedsenate =  Column(String(500))
    enacted =       Column(String(500))
    lastaction =    Column(String(500))
    link =          Column(String(500))
    published =     Column(String(500))
    committees =    Column(String(500))

engine = create_engine('sqlite:///legislators.db')
Base.metadata.create_all(engine)
