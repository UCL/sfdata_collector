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
import time
import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import BigInteger, Integer, Float, String, DateTime, \
                                Time


Base = declarative_base()

class SFparkRecord(Base):
    """ 
    Maps the object representation of a single availability (main) record of 
    SFPark data to its representation in a relational database.
        
    For information on the SFPark API, please see:     
    http://sfpark.org/resources/sfpark-availability-service-api-reference/
    
    A corresponding database, named sfdata, should be available, and contain
    a table with the following definition: 
        
    CREATE TABLE sfpark (
	id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,  # Unique ID and primary index
	availability_updated_timestamp DATETIME,   # Returns the Timestamp of when the availability data response was updated for the request
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
	lon2  NUMERIC(14,10),                      # Longitude point 2 for this location (specified only if PTS is 2)
	occ   INTEGER,                             # Number of spaces currently occupied  
	oper  INTEGER                              # Number of spaces currently operational for this location
    );
    """
    
    __tablename__ = 'sfpark'
    
    # Primary and unique ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)   

    # The Timestamp of when the availability data response was updated for the request
    availability_updated_timestamp = Column(DateTime)   
        
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
		
    # Number of spaces currently occupied 
    occ   = Column(Integer)               
	
    # Number of spaces currently operational for this location 
    oper  = Column(Integer) 
    
    # Relationships
    rates = relationship('SFparkRatesRecord', backref="sfpark")
    ophrs = relationship('SFparkOphrsRecord', backref="sfpark") 
    
    def __init__(self, updated_time, json):
        """
        Constructor. 
        
        *json* is a dictionary extracted directly from the json file that
        the SFpark API returns.  If they change their API, we will need to
        modify our code.
                
        For information on the SFPark API, please see:     
        http://sfpark.org/resources/sfpark-availability-service-api-reference/
        """
        
        self.availability_updated_timestamp     = updated_time
        if "TYPE"  in json: self.parktype      = json["TYPE"]           
        if "NAME"  in json: self.name          = json["NAME"]    
        if "DESC"  in json: self.descr         = json["DESC"]                
        if "INTER" in json: self.inter         = json["INTER"]                
        if "TEL"   in json: self.tel           = json["TEL"]                
        if "OSPID" in json: self.ospid         = int(json["OSPID"])                
        if "BFID"  in json: self.bfid          = int(json["BFID"])                
        if "PTS"   in json: self.pts           = int(json["PTS"])        
        if "OCC"   in json: self.occ           = int(json["OCC"])            
        if "OPER"  in json: self.oper          = int(json["OPER"])                  
        
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
        
        # parking rates records
        if "RATES" in json:
            if isinstance(json["RATES"]["RS"], list):
                for rates_json in json["RATES"]["RS"]:
                    rate = SFparkRatesRecord(rates_json)
                    self.rates.append(rate)
        
        # operating hours records
        if "OPHRS" in json:
            if isinstance(json["OPHRS"]["OPS"], list):
                for ophrs_json in json["OPHRS"]["OPS"]:
                    ophr = SFparkOphrsRecord(ophrs_json)
                    self.ophrs.append(ophr)
        

class SFparkRatesRecord(Base):
    """ 
    Maps the object representation of a single rates record of 
    SFPark data to its representation in a relational database.
        
    For information on the SFPark API, please see:     
    http://sfpark.org/resources/sfpark-availability-service-api-reference/
    
    A corresponding database, named sfdata, should be available, and contain
    a table with the following definition: 
        
    CREATE TABLE sfpark_rates (
	id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,  # Unique ID and primary index in this table
        sfpark_id BIGINT NOT NULL,                 # links to ID in table sfpark
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

    # links to ID in table sfpark
    sfpark_id = Column(BigInteger, ForeignKey('sfpark.id')) 
    
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

    def __init__(self, json):
        """
        Constructor. 
        
        *json* is a dictionary extracted directly from the json file that
        the SFpark API returns.  If they change their API, we will need to
        modify our code.
        
        For information on the SFPark API, please see:     
        http://sfpark.org/resources/sfpark-availability-service-api-reference/
        """

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
    SFPark data to its representation in a relational database.
        
    For information on the SFPark API, please see:     
    http://sfpark.org/resources/sfpark-availability-service-api-reference/
    
    A corresponding database, named sfdata, should be available, and contain
    a table with the following definition: 
        
    CREATE TABLE sfpark_ophrs (
	id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,  # Unique ID and primary index in this table
        sfpark_id BIGINT NOT NULL,                 # links to ID in table sfpark
	from_day  CHAR(16),                        # Start day for this schedule, e.g., Monday
	to_day    CHAR(16),                        # End day for this schedule, e.g., Friday
	beg       TIME,                            # Indicates the begin time for this schedule
	end       TIME                             # Indicates the end time for this schedule 
    ); 
    """
    
    __tablename__ = 'sfpark_ophrs'
    
    # Primary and unique ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)   

    # links to ID in table sfpark
    sfpark_id = Column(BigInteger, ForeignKey('sfpark.id'))               
    
    # Start day for this schedule, e.g., Monday
    from_day = Column(String(16))
    
    # End day for this schedule, e.g., Friday                           
    to_day = Column(String(16))

    # Indicates the begin time for this rate schedule
    beg = Column(DateTime)
    
    # Indicates the end time for this rate schedule                            
    end = Column(DateTime)

    def __init__(self, json):
        """
        Constructor. 
        
        *json* is a dictionary extracted directly from the json file that
        the SFpark API returns.  If they change their API, we will need to
        modify our code.
                
        For information on the SFPark API, please see:     
        http://sfpark.org/resources/sfpark-availability-service-api-reference/
        """
        
        if "FROM" in json: self.from_day = json["FROM"]
        if "TO"   in json: self.to_day   = json["TO"]
        if "BEG"  in json:       
            t = datetime.datetime.strptime(json["BEG"], "%I:%M %p")
            self.beg = t.time()
        if "END"  in json: 
            t = datetime.datetime.strptime(json["END"], "%I:%M %p")
            self.end = t.time()
        