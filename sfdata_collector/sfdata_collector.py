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
import sys
import datetime
import time
import thread

from sets import Set

import requests

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from SFparkDataModels import (Base, SFparkLocationRecord, 
                                 SFparkAvailabilityRecord, SFparkRatesRecord, 
                                 SFparkOphrsRecord)

USAGE = r"""

 python sfdata_collector.py dbstring
 
 dbstring - in the form: dialect+driver://user:password@host/dbname[?key=value..]
            see sqlalchemy documentation on create_engine() for options
 
 i.e. 'postgresql://username:password@localhost/sfdata'
   
 This script collects real time data from a range of different sources, 
 and stores the resulting data in a database.  

 Press Enter to quit. 
"""
 
# these globals are for tracking what we've stored previously to prevent
# keeping too many copies of the same data
storedLocations = Set()
lastDate = 0

def initializeSFparkData(session):
    """
    Figure out which locations have already been written to the database
    so we don't do it again.
    """
    for rec in session.query(SFparkLocationRecord):
        storedLocations.add(rec.id)


def collectSFparkData(session):
    """
    Makes a request to the SFpark server to get current parking availability,
    rates and operating hours.  
        
    For information on the SFPark API, please see:     
    http://sfpark.org/resources/sfpark-availability-service-api-reference/
    
    For stored data structure, see SFparkDataModels.py
    """
    
    # request data from the server
    sfpark_params = {'RADIUS':'50.0',        # Within 50 units of SF
                     'UOM':'mile',           # Units in miles
                     'RESPONSE':'json',      # Return in JSON format
                     'TYPE':'all',           # Both on-street and off-street
                     'PRICING':'yes'}        # Include pricing information
                     
    r = requests.get('http://api.sfpark.org/sfpark/rest/availabilityservice', 
                     params=sfpark_params)
    
    data = r.json()
    
    # create an object, and add to database
    if data["STATUS"]=="SUCCESS":
        
        # timestamp at top level
        string_time = data["AVAILABILITY_UPDATED_TIMESTAMP"].split('.')
        updated_time = datetime.datetime.strptime(string_time[0], "%Y-%m-%dT%H:%M:%S")
        date_id = 10000*updated_time.year + 100*updated_time.month + updated_time.day
    	    	
        global lastDate
        if date_id != lastDate:
            lastDate = date_id

            for avl in data["AVL"]: 
                
                # id is a combination of opsid and bfid
                if avl["TYPE"]=="OFF": 
                    loc_id = int(avl["OSPID"])
                else:
                    loc_id = int(avl["BFID"])

                # location gets added once 
                if loc_id not in storedLocations:
                    loc_record = SFparkLocationRecord(loc_id, avl)
                    session.add(loc_record)
                    storedLocations.add(loc_id)
                
                # update rates and operating hours once per day
                if "RATES" in avl:
                    if isinstance(avl["RATES"]["RS"], list):
                        for rates_json in avl["RATES"]["RS"]:
                            rates_record = SFparkRatesRecord(loc_id, date_id, rates_json)
                            session.add(rates_record)
        
                if "OPHRS" in avl:
                    if isinstance(avl["OPHRS"]["OPS"], list):
                        for ophrs_json in avl["OPHRS"]["OPS"]:
                            ophrs_record = SFparkOphrsRecord(loc_id, date_id, ophrs_json)
                            session.add(ophrs_record)
                

    	# update availability every time
        for avl in data["AVL"]: 
            # id is a combination of opsid and bfid
            if avl["TYPE"]=="OFF": 
                loc_id = int(avl["OSPID"])
            else:
                loc_id = int(avl["BFID"])

            avl_record = SFparkAvailabilityRecord(loc_id, date_id, updated_time, avl)            
            session.add(avl_record)            


    else:
        print data["ERROR_CODE"] + " " + data["MESSAGE"]

    session.commit()
        
def input_thread(L):
    """
    Utility function that allows the program to continue until
    the user hits enter. 
    """
    raw_input()
    L.append(None)
    
    
if __name__ == "__main__":
    
    # specify username and password at command line
    if len(sys.argv) <1:
        print USAGE
        sys.exit(2)
        
    dbstring = sys.argv[1]
 
    # initialize the database connection
    engine = create_engine(dbstring)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # track to make sure we don't overwrite stuff already in database
    initializeSFparkData(session)
    
    # some threading stuff to check for user input
    print "Press Enter to quit.  (Won't respond until end of wait period.)"
    L=[]
    thread.start_new_thread(input_thread, (L,))
    
    # the main loop
    while True:
        if L: break
        
        print "Working..."
        startTime = datetime.datetime.now()        
        collectSFparkData(session)
        
        print "  waiting."
        elapsedTime = datetime.datetime.now() - startTime
        if elapsedTime.total_seconds() < 60:
            time.sleep(60 - elapsedTime.total_seconds())
        

    # always close the session
    session.close()
    print "Thanks for collecting data.  Time for a pint!"
