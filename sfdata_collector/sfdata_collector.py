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
import requests

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from SFparkDataModels import Base, SFparkRecord

USAGE = r"""

 python sfdata_collector.py username password
 
 username - should be for mysql database existing on localhost
 password - should be for mysql database existing on lcoalhost
   
 This script collects real time data from a range of different sources, 
 and stores the resulting data in a database.  

"""
 
def collectSFparkData(session):
    """
    Makes a request to the SFpark server to get current parking availability,
    rates and operating hours.  
        
    For information on the SFPark API, please see:     
    http://sfpark.org/resources/sfpark-availability-service-api-reference/
    
    A corresponding MySQL database should exist and contain tables as 
    specified in SFparkRecord.py, SFparkRatesRecord.py, SFparkOphrsRecord.py.
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
    	
    	# all other attributes for each availability record
        for avl in data["AVL"]:            
            avl_record = SFparkRecord(updated_time, avl)            
            session.add(avl_record)

    else:
        print data["ERROR_CODE"] + " " + data["MESSAGE"]

    session.commit()
        
    
if __name__ == "__main__":
    
    # specify username and password at command line
    if len(sys.argv) <2:
        print USAGE
        sys.exit(2)

    username = sys.argv[1]
    password = sys.argv[2]
 
    # initialize the database connection
    engine = create_engine('mysql://'+username+':'+password+'@localhost/sfdata')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    #while True:
    for i in range(0,2):
        print "iteration %i" % i
        collectSFparkData(session)
        time.sleep(6)

    session.close()
