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

import pprint
import pymongo
import pandas as pd 
import numpy as np
import holoviews as hv
from holoviews import opts, dim
import plotly
import plotly.graph_objects as go
import plotly.express as pex


def genSankey(df,cat_cols=[],value_cols='',title='Sankey Diagram'):
    # maximum of 6 value cols -> 6 colors
    colorPalette = ['#A6206A', '#2F9395', '#F16A43', '#EC1C4B', '#F7D969']
    labelList = []
    colorNumList = []
    for catCol in cat_cols:
        labelListTemp=list(set(df[catCol].values))
        colorNumList.append(len(labelListTemp))
        labelList = labelList + labelListTemp

    # remove duplicates from labelList
    labelList = list(dict.fromkeys(labelList))

    # define colors based on number of levels
    colorList = []
    for idx, colorNum in enumerate(colorNumList):
        colorList = colorList + [colorPalette[idx]]*colorNum

    # transform df into a source-target pair
    for i in range(len(cat_cols)-1):
        if i==0:
            sourceTargetDf = df[[cat_cols[i],cat_cols[i+1],value_cols]]
            sourceTargetDf.columns = ['source','target','count']
        else:
            tempDf = df[[cat_cols[i],cat_cols[i+1],value_cols]]
            tempDf.columns = ['source','target','count']
            sourceTargetDf = pd.concat([sourceTargetDf,tempDf])
        sourceTargetDf = sourceTargetDf.groupby(['source','target']).agg({'count':'sum'}).reset_index()

    # add index for source-target pair
    sourceTargetDf['sourceID'] = sourceTargetDf['source'].apply(lambda x: labelList.index(x))
    sourceTargetDf['targetID'] = sourceTargetDf['target'].apply(lambda x: labelList.index(x))

    # creating the sankey diagram
    data = dict(type='sankey',
        node = dict(pad = 15, thickness = 20, line = dict(color = "black", width = 0.5), label = labelList, color = colorList),
        link = dict(source = sourceTargetDf['sourceID'], target = sourceTargetDf['targetID'], value = sourceTargetDf['count']))
    layout = dict(title=title, font=dict(size=20))

    fig = dict(data=[data], layout=layout)
    return fig

def plot_sankey_from_db(clients, filename_output):
    # general clients numbers
    client_list = [client for client in clients.find({})]
    client_list = [client for client in client_list  for game in client["game_history"] if game.get("gameId", None)=="sociodem_coact"]
    print(len(client_list))
    # index- and column names
    cat_labels = {"genere":{'m':"masculino", 'f':"feminino", 'd':"no-binario", 'nvr':"no dicho"}, "pp":{"Sí":"Sí", "No":"No", "nvr":"no indicado"}, "edat":{"1": "18-24", "2":"25-34", "3":"35-44", "4":"45-54", "5":"55-64", "6":"65+", "nvr":"no compartido"}}
    columns     = list(cat_labels.keys())# "relation",  "associated", "professional"     
    values_per_column = {column:[] for column in columns}
    
    for column in columns: 
        values_per_column[column] = list(set([ cat_labels[column][client[column]] for client in client_list]))
    #"convivencia", "familiar", "amistad", "laboral", "veïnat", "oci",

    N_participants = len(client_list)
    index_array = np.arange(N_participants)
    # create dataframe full of NaNs
    sankey_table = pd.DataFrame(index=index_array, columns=columns)
    for column in columns: 
        sankey_table[column] = [ cat_labels[column][client[column]] for client in client_list]
    
    grouped_sankey_table = sankey_table.groupby(columns).size().reset_index(name='counts')
    fig = genSankey(grouped_sankey_table, cat_cols=columns, value_cols='counts', title='Diagrama de Sankey con Género, Persona con problemas de Salut Mental y Edad')
    #fig['layout'] = [dict(title_font_size=20)]
    fig['layout']['annotations'] = [dict(x=0, y=1.05,text="Género", showarrow=False, font=dict(color='black', size=20)),
                                    dict(x=0.5, y=1.05,text="Primera Persona", showarrow=False, font=dict(color='black', size=20)),
                                    dict(x=1, y=1.05,text="Edad", showarrow=False, font=dict(color='black', size=20))]
    plot = plotly.offline.plot(fig, validate=False, filename = filename_output)
    return 
