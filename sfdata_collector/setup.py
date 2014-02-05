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

from distutils.core import setup
import py2exe

USAGE = r"""

 python setup.py py2exe 
 
 Script needs to find the paths, so easiest just to run from the current 
 directory.  It will create lots of output in the build and dist folders.
 What you want is everything in the dist/ directory.  To run, you need to make
 sure that directory is in your pathand then you will call sfdata_collector.exe. 
 
"""


setup(
    console=['sfdata_collector.py'] , 
    options = {
        'py2exe': {
        
            # this tells it to group everything into a single file
            # but it isn't supported for win64
            #'bundle_files': 1,
            
            # these are derived empirically.  
            # not sure why it doesn't figure them out on its own
            'packages': [
                'sqlalchemy.util', 
                'sqlalchemy.dialects'
            ], 
            
            # these are also derived empirically.  
            # not sure why it doesn't figure them out on its own
            'includes': [
                'sqlalchemy.util.queue'
            ]     
            
        }
    }
)
