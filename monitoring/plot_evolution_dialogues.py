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

"""
creates bokeh plot that shows exactly where which participant is in which dialogue, and when they answered which dialogues already.
Serves as monitor to see whether bot does what it should. 
"""

# caragar librarias
import os
import pymongo
import pprint
import pymongo
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from colormap import rgb2hex
from random import randint
import time
from datetime import date
import matplotlib
from matplotlib import dates as mdates
from matplotlib.ticker import MaxNLocator
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from minimal_mail import send_mail

#from minimal_mail import send_mail
from datetime import datetime
from bokeh.plotting import figure, output_file, show
from bokeh.layouts import layout
from bokeh.models import ColumnDataSource, CDSView, GroupFilter, HoverTool, Toggle, Label

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
bot       = database.bot # Quién está conectado al bot, cuál relatos ha visto, y como ha respondido?

# general clients numbers
client_list = [client for client in clients.find({})]

# story sequence
story_sequence = [bot for bot in bot.find({}) if bot['_id'] == 'objects_to_be_sent'][0]["list_relatosCT_plus"]

# figure properties
p = figure(title = "Dialogue timing for particpiants that entered LATER then us 6 ", x_axis_type="datetime", tools="hover,pan,wheel_zoom,box_zoom,reset", toolbar_location="right", plot_width=1500, name="dialogue timing")
p.xaxis.axis_label = 'time'
p.yaxis.axis_label = 'story'

# plot colors
hsv = cm.get_cmap('hsv', len(client_list))
colors_participants = hsv(range(len(client_list)))

# collect lines for toggle
user_circle, user_line = list(np.zeros(len(client_list))), list(np.zeros(len(client_list)))

# make a line for each particpant, a dot for each story start or end.
for count, client in enumerate(client_list):
    client0 = client_list[count]
    colors_participant = matplotlib.colors.to_hex(colors_participants[count])
    start_times, end_times, all_times, story_ids, indeces_in_sequence, durations, durations_in_hours, colors, gtypte, last_message = [], [], [], [], [], [], [], [], [], []
    game_hist = client0["game_history"]
    index_in_sequence = 0
    if game_hist:
        for idx, story in enumerate(game_hist):
            gtypte.append("game finished")
            gtypte.append("game finished")
            #client_id.append(client["_id"] ).append(client["_id"] )
            start_time = datetime.fromtimestamp(story["start_time"], tz = tz_M)
            end_time   = datetime.fromtimestamp(max(story["start_time"], story["end_time"]), tz = tz_M)
            start_times.append(start_time)
            start_times.append(start_time)
            end_times.append(end_time)
            end_times.append(end_time)
            all_times.append(start_time)
            all_times.append(end_time)
            last_message.append("NaN")
            last_message.append("NaN")
            story_ids.append(story["gameId"])
            story_ids.append(story["gameId"])
            if story["gameId"] in story_sequence:
                index_in_sequence = story_sequence.index(story["gameId"])
                colors.append("blue")
                colors.append("blue")
                #p.line([start_time, end_time], index_in_sequence*np.ones(2), color = 'blue') 
            else: 
                index_in_sequence = index_in_sequence+0.2
                colors.append("red")
                colors.append("red")
                #p.line([start_time, end_time], index_in_sequence*np.ones(2), color = 'red') 
            indeces_in_sequence.append(index_in_sequence+0.01*count)
            indeces_in_sequence.append(index_in_sequence+0.01*count)
            durations.append(story["end_time"]-story["start_time"])
            durations.append(story["end_time"]-story["start_time"])
            durations_in_hours.append((story["end_time"]-story["start_time"])//(60*60))
            durations_in_hours.append((story["end_time"]-story["start_time"])//(60*60))
    story = client0["current_game"]
    if story:
        gtypte.append("current game")
        gtypte.append("current game")
        #client_id.append(client["_id"] ).append(client["_id"] )
        start_time = datetime.fromtimestamp(story["start_time"], tz = tz_M)
        end_time   = datetime.now(tz = tz_M)
        start_times.append(start_time)
        start_times.append(start_time)
        end_times.append(end_time)
        end_times.append(end_time)
        all_times.append(start_time)
        all_times.append(end_time)
        story_ids.append(story["gameId"])
        story_ids.append(story["gameId"])
        last_message.append(story["last_message"][client["_id"]])
        last_message.append(story["last_message"][client["_id"]])
        if story["gameId"] in story_sequence:
            index_in_sequence = story_sequence.index(story["gameId"])
            colors.append("blue")
            colors.append("blue")
            #p.line([start_time, end_time], index_in_sequence*np.ones(2), color = 'gray') 
        else: 
            index_in_sequence = indeces_in_sequence[max(0, idx-1)]+0.2
            colors.append("red")
            colors.append("red")
            #p.line([start_time, end_time], index_in_sequence*np.ones(2), color = 'gray') 
        indeces_in_sequence.append(index_in_sequence+0.01*count)
        indeces_in_sequence.append(index_in_sequence+0.01*count)
        durations.append(story["end_time"]-story["start_time"])
        durations.append(story["end_time"]-story["start_time"])
        durations_in_hours.append((time.time()-story["start_time"])//(60*60))
        durations_in_hours.append((time.time()-story["start_time"])//(60*60))

    # collect plot and hover over information
    source = ColumnDataSource(data={
        "finished_or_not" : gtypte,
        "last_message" : last_message,
        #'client_id': client_id,
        'index in sequence' : indeces_in_sequence,
        'all_times' : all_times,
        'start_times' : start_times,
        'end_times'   : end_times,
        'dialogue'   : story_ids,
        'durations': durations,
        "durations_in_hours": durations_in_hours, 
        "colors": colors
        })

    # plot lines for participants and dots for stories; participants with status 0 get black lines/dots
    if client["status"] == 1:
        user_circle[count] = p.circle(x = 'all_times', y = 'index in sequence',
                color = colors_participant, fill_alpha=0.2, size=10, source = source)
        user_line[count] = p.line(x = 'all_times', y = 'index in sequence',
                color = colors_participant, source = source)
    elif client["status"] == 0:
        user_circle[count] = p.circle(x = 'all_times', y = 'index in sequence',
                color = "black", size=10, source = source, line_color = None)
        user_line[count] = p.line(x = 'all_times', y = 'index in sequence',
                color = "black", source = source, line_dash = "dashed" )

# define what is shon when hovering over 
p.add_tools(HoverTool(
    tooltips=[
        ("finished or not?", "@finished_or_not"),
        ('start time dialogue', '@start_times{%F %T}'),
        ('end time dialogue', '@end_times{%F %T}'),
        ('duration', '@durations{0.2f}s'),
        ('duration in hours >', '@durations_in_hours'),
        ('dialogue', '@dialogue'),
        ('last_message', '@last_message')
    ],
    formatters={
        '@gtypte'           : 'printf',
        '@start_times'      : 'datetime', # use 'datetime' formatter for 'date' field
        '@end_times'        : 'datetime', 
        '@dialogue'         : 'printf',
        "@last_message"     : "printf"#,   # use 'printf' formatter for 'adj close' field
        #'@duration' : 'printf'                        # use default 'numeral' formatter for other fields
    },

    # display a tooltip whenever the cursor is vertically in line with a glyph
    mode='vline'
))           

# one button per participant to hide/show  their line, and one to hide/show them all         
toggle = []
for i in range(len(client_list)//5+1):
    toggle.append([])
    for ii in range(5):
        iii = 5*i+ii
        if iii < len(client_list):
            toggle[i].append(Toggle(label="participant "+str(iii), button_type="success", active=True, max_width=200))
            toggle[i][ii].js_link('active', user_line[iii], 'visible')
toggle0 = Toggle(label="Todos", button_type="success", active=True, max_width=200, background="blue")
for iv in range(len(client_list)):
    toggle0.js_link('active', user_line[iv], 'visible')            
toggle[i].append(toggle0)           

# write ralat name to each line within th plot
data_lanzamiento =  date.fromisoformat('2021-07-13')
for i, story in enumerate(story_sequence):
    dialoguelabel = Label(x=data_lanzamiento, y=i, text_alpha=0.5, x_units='data', y_units='data',
                 text=story, render_mode='css')
    p.add_layout(dialoguelabel)

# output and send
show(layout([p], toggle)) 
output_file("./plot_evolution_dialogues.html")
send_mail("mail with bokeh plot", "content of the mail in <b>html</b>", attachment_path_list=["./plot_evolution_dialogues.html"])


