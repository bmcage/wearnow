#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2015       Benny Malengier
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from __future__ import print_function
""" 
   Logic to determine comfort related values
"""

def compute_comfort(db, ensemble_handle):
    insulation = []
    en = db.get_ensemble_from_handle(ensemble_handle)
    for childref in en.get_child_ref_list():
        gar = db.get_textile_from_handle(childref.ref)
        insulation += [3.]
        
    __compute_ensemble_comfort(insulation)
    
def __compute_ensemble_comfort(insulation, user, activity, climate):
    """ We compute from list of insulation, ... what comfort will be
    """
    #TODO
    result = 0.
    result = user['Weight'] * climate['T'] / insulation[0]
    return result
    
if __name__ == "__main__": 
    #test to determine if our comfort function works
    user = {
        'name'      : "Ahmed Mahmood",
        'Weight'    : 68,               # kg
        }
    climate = {
        'T'         : 21,   # degrees Celcius
        'v_air'     : 6,    # m/s
        }
    activity = {
        'type'      : 'SPORT'
        }
    #ensemble data: [trouser, pullover]
    insulation = [1.3, 2.3]  # unit ???
    #compute
    result = __compute_ensemble_comfort(insulation, user, activity, climate)
    #finished
    print ('The resulting comfort is', result)
