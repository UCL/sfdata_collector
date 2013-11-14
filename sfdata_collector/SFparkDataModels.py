# -*- coding: utf-8 -*-
__author__      = "Gregory D. Erhardt"
__copyright__   = "Copyright 2013 SFCTA"
__license__     = """
    This file is part of sfdata_collector.

    sfdata_collector is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    sfdata_collector is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with sfdata_collector.  If not, see <http://www.gnu.org/licenses/>.
"""

import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import (BigInteger, Integer, Float, String, DateTime, 
                                Time)

Base = declarative_base()

class SFparkLocationRecord(Base):
    """ 
    Maps the object representation of a single parking location (off-street 
    lot or block face) record of SFPark data to its representation in a 
    relational database.  There is only a single intance for each location,
    although the data are updated with each query in case new lots come 
    online.
        
    For information on the SFPark API, please see:     
    http://sfpark.org/resources/sfpark-availability-service-api-reference/
    
    A corresponding database, named sfdata, should be available, and contain
    a table with the following definition: 
        
    CREATE TABLE sfpark_loc (
	id INT NOT NULL PRIMARY KEY,               # Unique ID and primary index (combination of opsid and bfid)
	parktype CHAR(3),                          # Specifies whether on or off street parking 
	name  VARCHAR(255),                        # Name of parking location or street with from and to address if available 
	descr VARCHAR(255),                        # Returned for OSP only – usually address for the parking location if available 
	inter VARCHAR(255),                        # Returned for OSP only – usually cross street intersection parking location if available 
	tel   VARCHAR(255),                        # Returned for OSP only – Contact telephone number for parking location if available 
	ospid INTEGER,                             # Unique SFMTA Identifier for the parking location for off street parking type 
	bfid  INTEGER,                             # Unique SFMTA Identifier for on street block face parking  
	pts   INTEGER,                             # Number of location points returned for this record. Usually 1 for OSP and 2 for on-street parking location  
	lat1  NUMERIC(14,10),                      # Latitude point 1 for this location (specified for all sites)
	lon1  NUMERIC(14,10),                      # Longitude point 1 for this location (specified for all sites)
	lat2  NUMERIC(14,10),                      # Latitude point 2 for this location (specified only if PTS is 2)
	lon2  NUMERIC(14,10)                       # Longitude point 2 for this location (specified only if PTS is 2)
    );
    """
    
    __tablename__ = 'sfpark_loc'
    
    # Primary and unique ID
    id = Column(Integer, primary_key=True)   

    # Specifies whether on or off street parking 
    parktype  = Column(String(3))             
    
    # Name of parking location or street with from and to address if available           
    name  = Column(String(255))    
	
    # Returned for OSP only – usually address for the parking location if available 	
    descr = Column(String(255))                         
	
    # Returned for OSP only – usually cross street intersection parking location if available 
    inter = Column(String(255))                         
    
    # Returned for OSP only – Contact telephone number for parking location if available 
    tel   = Column(String(255))                         

    # Unique SFMTA Identifier for the parking location for off street parking type 
    ospid = Column(Integer)                             
	
    # Unique SFMTA Identifier for on street block face parking  
    bfid  = Column(Integer)                             
	
    # Number of location points returned for this record. Usually 1 for OSP and 2 for on-street parking location 
    pts   = Column(Integer)                              
	
    # Latitude point 1 for this location (specified for all sites)
    lat1  = Column(Float)                      
	
    # Longitude point 1 for this location (specified for all sites)
    lon1  = Column(Float)                      
	
    # Latitude point 2 for this location (specified only if PTS is 2)
    lat2  = Column(Float)                      
	
    # Longitude point 2 for this location (specified only if PTS is 2)
    lon2  = Column(Float)             
		    
    # Relationships
    avail = relationship('SFparkAvailabilityRecord', backref="sfpark_loc")
    rates = relationship('SFparkRatesRecord', backref="sfpark_loc")
    ophrs = relationship('SFparkOphrsRecord', backref="sfpark_loc") 
    
    def __init__(self, loc_id, json):
        """
        Constructor. 
        
        *json* is a dictionary extracted directly from the json file that
        the SFpark API returns.  Feed this the AVL record, which contains
        location information. 
                
        """        
        
        # the data attributes
        self.id = loc_id
        if "TYPE"  in json: self.parktype      = json["TYPE"]           
        if "NAME"  in json: self.name          = json["NAME"]    
        if "DESC"  in json: self.descr         = json["DESC"]                
        if "INTER" in json: self.inter         = json["INTER"]                
        if "TEL"   in json: self.tel           = json["TEL"]                
        if "OSPID" in json: self.ospid         = int(json["OSPID"])                
        if "BFID"  in json: self.bfid          = int(json["BFID"])                
        if "PTS"   in json: self.pts           = int(json["PTS"])                    
                
        # This is in the order specified by the SFpark API
        if "LOC" in json:
            loc = json["LOC"].split(',')
            if self.pts==1:
                self.lat1 = float(loc[1])
                self.lon1 = float(loc[0])
            elif self.pts==2:  
                self.lat1 = float(loc[1])
                self.lon1 = float(loc[0])
                self.lat2 = float(loc[3])
                self.lon2 = float(loc[2])
                

class SFparkAvailabilityRecord(Base):
    """ 
    Maps the object representation of a single availability (main) record of 
    SFPark data to its representation in a relational database.  These will
    be udpated every minute. 
        
    A corresponding database, named sfdata, should be available, and contain
    a table with the following definition: 
        
    CREATE TABLE sfpark_avl (
	id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,  # Unique ID and primary index
	loc_id INT NOT NULL,                       # ID to link back to location table
	date_id INT NOT NULL,                      # date ID in form YYYYMMDD
	availability_updated_timestamp DATETIME,   # Returns the Timestamp of when the availability data response was updated for the request
	occ   INTEGER,                             # Number of spaces currently occupied  
	oper  INTEGER                              # Number of spaces currently operational for this location
    );
    """
    
    __tablename__ = 'sfpark_avl'
    
    # Primary and unique ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)   

    # links to ID in location table
    loc_id = Column(BigInteger, ForeignKey('sfpark_loc.id')) 
    
    # date ID: integer in YYYYMMDD form
    date_id = Column(Integer)
    
    # The Timestamp of when the availability data response was updated for the request
    availability_updated_timestamp = Column(DateTime)   
    
    # Number of spaces currently occupied 
    occ   = Column(Integer)               
	
    # Number of spaces currently operational for this location 
    oper  = Column(Integer) 
        
    def __init__(self, loc_id, date_id, updated_time, json):
        """
        Constructor. 

        *loc_id* the location ID from the related record
        
        *date_id* the date ID in the form YYYYMMDD
        
        *updated_time* extracted from the main json record, the updated time
        is the datetime when the availabilities were last updated. 
        
        *json* is a dictionary extracted directly from the json file that
        the SFpark API returns.  Feed this the AVL record.
        
        """
        
        self.loc_id = loc_id
        self.date_id = date_id
        self.availability_updated_timestamp    = updated_time     
        if "OCC"   in json: self.occ           = int(json["OCC"])            
        if "OPER"  in json: self.oper          = int(json["OPER"])                  
        
        
        
class SFparkRatesRecord(Base):
    """ 
    Maps the object representation of a single rates record of 
    SFPark data to its representation in a relational database.  These will
    be updated every day.  
            
    A corresponding database, named sfdata, should be available, and contain
    a table with the following definition: 
        
    CREATE TABLE sfpark_rates (
	id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,  # Unique ID and primary index in this table
	loc_id INT NOT NULL,                       # ID to link back to location table
	date_id INT NOT NULL,                      # date ID in form YYYYMMDD
	beg       TIME,                            # Indicates the begin time for this rate schedule
	end       TIME,                            # Indicates the end time for this rate schedule 
	rate      NUMERIC(8,2),                    # Applicable rate for this rate schedule
	descr     VARCHAR(255),                    # Used for descriptive rate information when not possible to specify using BEG or END times for this rate schedule
	rq        CHAR(16),                        # Rate qualifier for this rate schedule e.g. PerHr
	rr        VARCHAR(255)                     # Rate restriction for this rate schedule if any
    ); 
    """
    
    __tablename__ = 'sfpark_rates'
    
    # Primary and unique ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)   

    # links to ID in location table
    loc_id = Column(BigInteger, ForeignKey('sfpark_loc.id')) 
    
    # date ID: integer in YYYYMMDD form
    date_id = Column(Integer)
        
    # Indicates the begin time for this rate schedule
    beg = Column(Time)
    
    # Indicates the end time for this rate schedule                            
    end = Column(Time)
    
    # Applicable rate for this rate schedule
    rate = Column(Float)
    
    # Used for descriptive rate information when not possible to specify using BEG or END times for this rate schedule
    descr = Column(String(255))
    
    # Rate qualifier for this rate schedule e.g. PerHr                   
    rq = Column(String(16))

    # Rate restriction for this rate schedule if any                        
    rr = Column(String(255))                   

    def __init__(self, loc_id, date_id, json):
        """
        Constructor. 

        *loc_id* the location ID from the related record
        
        *date_id* the date ID in the form YYYYMMDD
        
        *json* is a dictionary extracted directly from the json file that
        the SFpark API returns.  This is the RATES portion within the AVL 
        record.        
        """

        self.loc_id = loc_id
        self.date_id = date_id
        if "BEG"  in json:       
            t = datetime.datetime.strptime(json["BEG"], "%I:%M %p")
            self.beg = t.time()
        if "END"  in json: 
            t = datetime.datetime.strptime(json["END"], "%I:%M %p")
            self.end = t.time()
        if "RATE" in json: self.rate  = float(json["RATE"])
        if "DESC" in json: self.descr = json["DESC"]
        if "RQ"   in json: self.rq    = json["RQ"]
        if "RR"   in json: self.rr    = json["RR"]
        
        

class SFparkOphrsRecord(Base):
    """ 
    Maps the object representation of a single operating hours record of 
    SFPark data to its representation in a relational database.  This is the
    OPHRS portion of the AVL record. 
    
    A corresponding database, named sfdata, should be available, and contain
    a table with the following definition: 
        
    CREATE TABLE sfpark_ophrs (
	id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,  # Unique ID and primary index in this table
	loc_id INT NOT NULL,                       # ID to link back to location table
	date_id INT NOT NULL,                      # date ID in form YYYYMMDD
	from_day  CHAR(16),                        # Start day for this schedule, e.g., Monday
	to_day    CHAR(16),                        # End day for this schedule, e.g., Friday
	beg       TIME,                            # Indicates the begin time for this schedule
	end       TIME                             # Indicates the end time for this schedule 
    ); 
    """
    
    __tablename__ = 'sfpark_ophrs'
    
    # Primary and unique ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)      

    # links to ID in location table
    loc_id = Column(BigInteger, ForeignKey('sfpark_loc.id')) 
    
    # date ID: integer in YYYYMMDD form
    date_id = Column(Integer)      
    
    # Start day for this schedule, e.g., Monday
    from_day = Column(String(16))
    
    # End day for this schedule, e.g., Friday                           
    to_day = Column(String(16))

    # Indicates the begin time for this rate schedule
    beg = Column(DateTime)
    
    # Indicates the end time for this rate schedule                            
    end = Column(DateTime)

    def __init__(self, loc_id, date_id, json):
        """
        Constructor. 

        *loc_id* the location ID from the related record
        
        *date_id* the date ID in the form YYYYMMDD
        
        *json* is a dictionary extracted directly from the json file that
        the SFpark API returns.  If they change their API, we will need to
        modify our code.
                
        For information on the SFPark API, please see:     
        http://sfpark.org/resources/sfpark-availability-service-api-reference/
        """
        
        self.loc_id = loc_id
        self.date_id = date_id
        if "FROM" in json: self.from_day = json["FROM"]
        if "TO"   in json: self.to_day   = json["TO"]
        if "BEG"  in json:       
            t = datetime.datetime.strptime(json["BEG"], "%I:%M %p")
            self.beg = t.time()
        if "END"  in json: 
            t = datetime.datetime.strptime(json["END"], "%I:%M %p")
            self.end = t.time()
                
        