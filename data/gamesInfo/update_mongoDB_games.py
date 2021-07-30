"""
    CoActuem per la Salut Mental Chatobot
    Copyright (C) Franziska Peter

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# loads all jsons in this folder into the selected mongoDB database into the 
# collection gamesInfo

import os

# set mongoDB
database = "experiment_db" 

# set mongoimport mode: upsert means: 
"""Replace existing documents in the database with matching documents 
from the import file. mongoimport will insert all other documents."""
mode = "upsert" # <insert|upsert|merge|delete>


def list_files(directory, extension):
    """
    lists all files in the directory that have that 
    """
    return [f for f in os.listdir(directory) if f.endswith('.' + extension)]

for name_of_json_with_game in list_files("./", "json"):
    print(name_of_json_with_game)
    os.system("mongoimport -d " + database + " -c gamesInfo --mode="+ mode + " " + name_of_json_with_game)
