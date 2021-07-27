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
