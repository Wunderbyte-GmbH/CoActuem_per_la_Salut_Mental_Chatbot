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

#!/usr/bin/env python3

# caragar librarias
import os
import pymongo
import pprint
import pymongo
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import dates as mdates
from matplotlib.ticker import MaxNLocator
from minimal_mail import send_mail
from sankey_plot_from_db import plot_sankey_from_db
from datetime import datetime

# working directory, to know where imgs are stored
here = os.path.dirname(__file__) 

# time
from datetime import datetime
import time
import pytz as tz
tz_M = tz.timezone("Europe/Vienna")

# cargar datos de la base de datos
dbclient  = pymongo.MongoClient(serverSelectionTimeoutMS=1000)
database  = dbclient.experiment_db
gamesInfo = database.gamesInfo # contenidos relatos
clients   = database.clients # Quién está conectado al bot, cuál relatos ha visto, y como ha respondido?

# general clients numbers
client_list = [client for client in clients.find({})]

################ SAME PLOT FOR ALL CHARACTERISTICS #############################

def plot_num_part_over_time(entry_dates, category, legend_labels):
    """
    plots temporal evolution of number of participants with different features
    that are stored in the keys, such as different gernders, ages, or affected persons
    """
    # get all dates to be able to adapt x axis 
    all_dates = [x for key in entry_dates.keys() for x in entry_dates[key]]
    # generate plot 
    f, ax = plt.subplots(figsize = (10,6))
    plt.title("Timestamp of when participant first started the welcome dialogue")
    # add lines and dots for each category
    for count, key in enumerate(entry_dates.keys()):
        color = "C"+str(count%10)
        ax.plot(entry_dates[key], np.arange(len(entry_dates[key]))+1,"o",  color = color, alpha=0.5, label = legend_labels[key])
        ax.plot(entry_dates[key], np.arange(len(entry_dates[key]))+1, color = color, alpha=0.5)
    plt.legend(title = category)
    plt.gcf().autofmt_xdate()

    # y axis
    ax.set_ylabel("number participants")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # x axis
    ax.set_xlabel("welcome started")
    xformatter = mdates.DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(xformatter)
    locator = mdates.DayLocator(interval=(max(all_dates)-min(all_dates)).days//5)
    ax.xaxis.set_major_locator(locator)
    minlocator = mdates.DayLocator(interval=1)
    ax.xaxis.set_minor_locator(minlocator)

    # save figure as png
    plot_filename= here + "/img/"+category+"_vs_time_"+datetime.now().strftime("%d_%m_%Y")+".png"
    plt.savefig(plot_filename)
    return (plot_filename)

def gen_entry_dates(category_dict, db_name_category):
    """
    create dict with different representatives of each category (e.g male, 
    female of gender) as keys and empty lists as vales that will later be filled
    with datetimestamps of when the participant first started the welcome dialogue
    """
    entry_dates = {db_label:[] for db_label in category_dict.keys()}
    for client in client_list:
        if client["current_game"] and client["current_game"]["gameId"] == "welcome":
            time_first_welcome_started = client["current_game"]["start_time"]
        else:
            time_first_welcome_started = min([x['start_time'] for x in client['game_history'] if x['gameId'] == 'welcome'])
        as_date = datetime.fromtimestamp(time_first_welcome_started, tz = tz_M)
        key = client.get(db_name_category, "not yet categorized")
        entry_dates[key] += [as_date]
        entry_dates["total"] += [as_date]
    return entry_dates


################# ENTERING DATE GENDER (started welcome) #######################
gender_dict = {"total":"en total", "f": "femino", "m":"masculino", "d":"no binario", "nvr":"no ha respondido", "not yet categorized":"no ha acabado sociodem"}
entry_dates = gen_entry_dates(gender_dict, "genere")
gender_plot = plot_num_part_over_time(entry_dates, "gender", gender_dict)

################# ENTERING DATE AGE (started welcome) #######################
age_dict = {"total":"en total", "1": "18-24", "2":"25-34", "3":"35-44", "4":"45-54", "5":"55-64", "6":"65+", "nvr":"no ha respondido", "not yet categorized":"no ha acabado sociodem"}
entry_dates = gen_entry_dates(age_dict, "edat")
age_plot = plot_num_part_over_time(entry_dates, "age", age_dict)

################# ENTERING DATE AGE (started welcome) #######################
pp_dict = {"total":"en total", "Sí":"si", "No":"no", "nvr":"no ha respondido", "not yet categorized":"no ha acabado sociodem"}
entry_dates = gen_entry_dates(pp_dict, 'pp')
pp_plot = plot_num_part_over_time(entry_dates, "affected_person", pp_dict)

#################### SANKEY PLOT #############################################
filename_sankey_plot = (here + "/img/sankey_"+datetime.now().strftime("%d_%m_%Y")+".html")
plot_sankey_from_db(clients, filename_sankey_plot)
################# now gather mail ############################################
# join this info to one phrase in html
gen_stats_text  = "<p>Hello team,</p>"
gen_stats_text += "<p>this is the weekly mail"
gen_stats_text += "</p></br></br>"

send_mail("CoAct chatbot weekly monitoring mail", gen_stats_text, attachment_path_list=[gender_plot, age_plot, pp_plot, filename_sankey_plot])
# output for cronjob
print("weekly mail send on: ", datetime.now())
