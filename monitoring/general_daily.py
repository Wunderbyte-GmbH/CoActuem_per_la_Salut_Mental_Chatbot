#!/usr/bin/env python3

# caragar librarias
import pymongo
import numpy as np
import time
from minimal_mail import send_mail
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import pprint 

# where should table of second part be saved?
filename_table_with_stats = "./table_categories_total_7d_24h.png"

# cargar datos de la base de datos
dbclient  = pymongo.MongoClient(serverSelectionTimeoutMS=1000)
database  = dbclient.experiment_db
gamesInfo = database.gamesInfo # contenidos relatos
clients   = database.clients # Quién está conectado al bot, cuál relatos ha visto, y como ha respondido?

# time constants
now       = time.time()
h24in_sec = 24*60*60
d7in_sec  = 7*24*60*60

# convert collection to list of dicts
client_list = [client for client in clients.find({})]
games_list  = [game for game in gamesInfo.find({})]

################# FIRST PART OF MAIL: continous text ####################################

# count entries in clients collection to get numbers of participants
num_clients_entries = len(client_list)

# count users sala de entrada, de altas, de bajos
status0 = len([1 for client in client_list if client['status']==0])
status1 = len([1 for client in client_list if client['status']==1])
status2 = len([1 for client in client_list if client['status']==2])
status3 = len([1 for client in client_list if client['status']==3])

# first paragraph: participant status
status_text  = "<H3>Participantes total que han entrado al xatbot: "+str(num_clients_entries)+"</H3>"
status_text += "<p>Participantes en la sala de entrada: ".ljust(40)+ str(status0)+"      (= welcome denegado o todavía no terminado)<br>"
status_text += "Participantes activos: ".ljust(37)              + str(status1)+"<br>"
status_text += "Participantes en pausa: ".ljust(37)             + str(status2)+"<br>"
status_text += "Participantes de baja: ".ljust(37)              + str(status3)+"</p>"

# count how many users passed welcome, capacitation, sociodem_1, sociodem_2, sociodem_3 
list_of_game_history_name_lists = [[story['gameId'] for story in client['game_history']] for client in client_list]
num_wel  = sum(1 for x in list_of_game_history_name_lists if "welcome" in x)
num_cap  = sum(1 for x in list_of_game_history_name_lists if "capacitation_Teatre_Amigues" in x)
num_soc  = sum(1 for x in list_of_game_history_name_lists if "sociodem_coact" in x)

# count how many users, of those who passed welcome denied and accepted the IC, respectively
list_of_game_history_lists = [[story for story in client['game_history'] if story['gameId']=="welcome"] for client in client_list]
list_of_nonempty_game_history_lists = [x for x in list_of_game_history_lists if x]
list_of_latest_game_history_lists = [[element for idx, element in enumerate(x) if x[idx]["end_time"] == max([value["end_time"] for value in x])] if len(x)>1 else x for x in list_of_nonempty_game_history_lists]
num_IC_yes = sum(1 for x in list_of_latest_game_history_lists if x[0]["answers"]["legal"]=="Si")
num_IC_no  = sum(1 for x in list_of_latest_game_history_lists if x[0]["answers"]["legal"]=="No")

# second paragraph: participant progress entering phase
progress_entry_text  = "<H3>Participantes que ya han terminado: </H3>"
progress_entry_text += "<p>Welcome: ".ljust(34)                     + str(num_wel)+"<br>"   
progress_entry_text += "... de ell@s confirmaron IC: ".ljust(31)+ str(num_IC_yes)+"<br>"
progress_entry_text += "... de ell@s rechazaron IC: ".ljust(31)  + str(num_IC_no)+"<br>"
progress_entry_text += "Capacitación: ".ljust(31)                + str(num_cap)+"<br>"
progress_entry_text += "Sociodem: ".ljust(31)                    + str(num_soc)+"</p>"

# only last week 
list_of_game_history_lists_started_and_finished_last_week  = [[story['gameId'] for story in client['game_history'] if (now - story['start_time']) < d7in_sec] for client in client_list]
list_of_game_history_lists_started_but_not_finished_last_week  = [[story['gameId'] for story in [client['current_game']] if (now - story['start_time']) < d7in_sec] for client in client_list if client["current_game"]!=None]
list_of_game_history_lists_started_last_week  = list_of_game_history_lists_started_and_finished_last_week + list_of_game_history_lists_started_but_not_finished_last_week
list_of_game_history_lists_finished_last_week = [[story['gameId'] for story in client['game_history'] if (now - story['end_time']) < d7in_sec] for client in client_list]
num_wel_s7d  = sum(1 for x in list_of_game_history_lists_started_last_week if "welcome" in x)
num_wel_f7d  = sum(1 for x in list_of_game_history_lists_finished_last_week if "welcome" in x)

# IC denied last week list_of_latest_game_history_lists
num_IC_no_7d  = sum(1 for x in list_of_latest_game_history_lists if (now - x[0]['end_time']) < d7in_sec and x[0]["answers"]["legal"]=="No")

# third paragraph: 7 days
entry7d_entry_text  = "<H3>En los últimos 7 días:  </H3>"
entry7d_entry_text += "<p>Participantes que empezaron el diálogo welcome: ".ljust(50)  + str(num_wel_s7d)+"<br>"   
entry7d_entry_text += "Participantes que acabaron el diálogo welcome: ".ljust(48)   + str(num_wel_f7d)+"<br>"
entry7d_entry_text += "Participantes que rechazaron el IC:  ".ljust(48)             + str(num_IC_no_7d)+"</p>"

# only last day \
list_of_game_history_lists_started_and_finished_last_week  = [[story['gameId'] for story in client['game_history'] if (now - story['start_time']) < h24in_sec] for client in client_list]
list_of_game_history_lists_started_but_not_finished_last_week  = [[story['gameId'] for story in [client['current_game']] if (now - story['start_time']) < h24in_sec] for client in client_list if client["current_game"]!=None]
list_of_game_history_lists_started_last_week  = list_of_game_history_lists_started_and_finished_last_week + list_of_game_history_lists_started_but_not_finished_last_week
list_of_game_history_lists_finished_last_week = [[story['gameId'] for story in client['game_history'] if (now - story['end_time']) < h24in_sec] for client in client_list]
num_wel_s24h  = sum(1 for x in list_of_game_history_lists_started_last_week if "welcome" in x)
num_wel_f24h  = sum(1 for x in list_of_game_history_lists_finished_last_week if "welcome" in x)

# IC denied last day list_of_latest_game_history_lists
num_IC_no_24h  = sum(1 for x in list_of_latest_game_history_lists if (now - x[0]['end_time']) < h24in_sec and x[0]["answers"]["legal"]=="No")

# fourth paragraph: 24h
entry24h_entry_text  = "<H3>En los últimos 24h:  </H3>"
entry24h_entry_text += "<p>Participantes que empezaron el diálogo welcome: ".ljust(50)  + str(num_wel_s24h)+"<br>"   
entry24h_entry_text += "Participantes que acabaron el diálogo welcome: ".ljust(48)   + str(num_wel_f24h)+"<br>"
entry24h_entry_text += "Participantes que rechazaron el IC:  ".ljust(48)             + str(num_IC_no_24h)+"</p>"

gen_stats_text = status_text + progress_entry_text + entry7d_entry_text + entry24h_entry_text 

################# SECOND PART OF MAIL: table with stats ####################################

title = "<H3>Tipología de los participantes (que han acabado el sociodem: "+str(num_soc)+")</H3>"
gen_stats_text += title

# index- and column names
array_super_index = np.array(["Gènere", "Gènere", "Gènere", "Gènere", 
                         "Edat", "Edat", "Edat", "Edat", "Edat", "Edat", "Edat",
                        "Participants amb problemes de salut mental", "Participants amb problemes de salut mental", "Participants amb problemes de salut mental",
                        "Cuidador", "Cuidador", "Cuidador",
                        "Ni primera persona ni cuidador (2x 'No')",
                        "Ni primera persona ni cuidador (2x 'No' o 'nvr')",
                         "Participants en relació amb persones amb problemes de salut mental", "Participants en relació amb persones amb problemes de salut mental", "Participants en relació amb persones amb problemes de salut mental", "Participants en relació amb persones amb problemes de salut mental", "Participants en relació amb persones amb problemes de salut mental", "Participants en relació amb persones amb problemes de salut mental",
                        "Relació amb associacions salut mental", "Professional de la salut mental"])
array_sub_index   = np.array(["m", "f", "d", "nvr", 
                         "18-24", "25-34", "35-44", "45-54", "55-64", "65+", "nvr",
                         "Sí", "No", "nvr",
                         "Sí", "No", "nvr",
                         " ",
                         " ",
                         "convivència", "familiar", "amistad", "laboral", "veïnat", "oci",
                         "Sí", "Sí"
                         ])
index_array   = [array_super_index, array_sub_index]
columns_array = ["24h", "7d", "total"]

# create dataframe full of NaNs
info_table = pd.DataFrame(index=index_array, columns=columns_array)

# filter for sociodem DONE24h, DONE7d, DONE ## LATER> split into 3
sociodem_list_done24h = [client for client in client_list if "sociodem_coact" in [story["gameId"] for story in client['game_history']] and next(story for story in client['game_history'] if story["gameId"] == "sociodem_coact")['end_time']>(now-h24in_sec)]
sociodem_list_done7d  = [client for client in client_list if "sociodem_coact" in [story["gameId"] for story in client['game_history']] and next(story for story in client['game_history'] if story["gameId"] == "sociodem_coact")['end_time']>(now-d7in_sec )]
sociodem_list_done    = [client for client in client_list if "sociodem_coact" in [story["gameId"] for story in client['game_history']]]

# fill gender
for gender in ["m", "f", "d", "nvr"]:
    info_table.loc[("Gènere", gender)] = [str(sum(1 for client in sociodem_list_done24h if client["genere"] == gender)),
                                          str(sum(1 for client in sociodem_list_done7d  if client["genere"] == gender)),
                                          str(sum(1 for client in sociodem_list_done    if client["genere"] == gender))]

# fill edat
#dict edat: db-identifier:text_written_on_button
dict_edat = {"1":"18-24", "2":"25-34", "3":"35-44", "4":"45-54", "5":"55-64", "6":"65+", "nvr":"nvr"}
for edat in ["1", "2", "3", "4", "5", "6", "nvr"]:
    info_table.loc[("Edat", dict_edat[edat])] = [str(sum(1 for client in sociodem_list_done24h if client["edat"] == edat)),
                                       str(sum(1 for client in sociodem_list_done7d  if client["edat"] == edat)),
                                       str(sum(1 for client in sociodem_list_done    if client["edat"] == edat))]

# fill Participants amb problemes de salut mental
for personal in ["Sí", "No", "nvr"]:
    info_table.loc[("Participants amb problemes de salut mental", personal)] = [str(sum(1 for client in sociodem_list_done24h if client["pp"] == personal)),
                                          str(sum(1 for client in sociodem_list_done7d  if client["pp"] == personal)),
                                          str(sum(1 for client in sociodem_list_done    if client["pp"] == personal))]

# fill Cuidador
for cuidador in ["Sí", "No", "nvr"]:
    info_table.loc[("Cuidador", cuidador)] = [str(sum(1 for client in sociodem_list_done24h if client["p_cuid"] == cuidador)),
                                          str(sum(1 for client in sociodem_list_done7d  if client["p_cuid"] == cuidador)),
                                          str(sum(1 for client in sociodem_list_done    if client["p_cuid"] == cuidador))]

# fill neither amb problemes de salut mental nor Cuidador
info_table.loc[("Ni primera persona ni cuidador (2x 'No')", " ")] = [str(sum(1 for client in sociodem_list_done24h if client["p_cuid"] == "No" and client["pp"] == "No")),
                                                                         str(sum(1 for client in sociodem_list_done7d  if client["p_cuid"] == "No" and client["pp"] == "No")),                                          str(sum(1 for client in sociodem_list_done     if client["p_cuid"] == "No" and client["pp"] == "No"))]


info_table.loc[("Ni primera persona ni cuidador (2x 'No' o 'nvr')", " ")]  = [str(sum(1 for client in sociodem_list_done24h if client["p_cuid"] != "Sí" and client["pp"] != "Sí")),
                                                                          str(sum(1 for client in sociodem_list_done7d  if client["p_cuid"] != "Sí" and client["pp"] != "Sí")),
                                                                          str(sum(1 for client in sociodem_list_done     if client["p_cuid"] != "Sí" and client["pp"] != "Sí"))]
# fill relation
dict_relation = {"p_c":"convivència", "p_f":"familiar", "p_a":"amistad", "p_l":"laboral", "p_v":"veïnat", "p_ac":"oci"}
for relation in ["p_c", "p_f", "p_a", "p_l", "p_v", "p_ac"]:
    info_table.loc[("Participants en relació amb persones amb problemes de salut mental", dict_relation[relation])] = [str(sum(1 for client in sociodem_list_done24h if client[relation] == "Sí")),
                                          str(sum(1 for client in sociodem_list_done7d  if client[relation] == "Sí")),
                                          str(sum(1 for client in sociodem_list_done    if client[relation] == "Sí"))]

# fill association
info_table.loc[("Relació amb associacions salut mental", "Sí")] = [str(sum(1 for client in sociodem_list_done24h if client["p_ass"] == "Sí")),
                                       str(sum(1 for client in sociodem_list_done7d  if client["p_ass"] == "Sí")),
                                       str(sum(1 for client in sociodem_list_done    if client["p_ass"] == "Sí"))]
# fill profession
info_table.loc[("Professional de la salut mental", "Sí")] = [str(sum(1 for client in sociodem_list_done24h if client["p_prof"] == "Sí")),
                                       str(sum(1 for client in sociodem_list_done7d  if client["p_prof"] == "Sí")),
                                       str(sum(1 for client in sociodem_list_done    if client["p_prof"] == "Sí"))]    
gen_stats_text += info_table.to_html()

################# second part of SECOND PART OF MAIL: table with stats ####################################

title = "<H3>Equilibrio entre grupos</H3>"
gen_stats_text += title

# index- and column names
array_super_index = np.array(["Participants amb problemes de salut mental",
                        "Cuidador",
                        "Ni primera persona ni cuidador (2x 'No')",
                        "Ni primera persona ni cuidador (2x 'No' o 'nvr')"])

index_array   = array_super_index
columns_array = ["24h", "7d", "total"]

# create dataframe full of NaNs
info_table = pd.DataFrame(index=index_array, columns=columns_array)

# filter for sociodem DONE24h, DONE7d, DONE ## LATER> split into 3
sociodem_list_done24h = [client for client in client_list if "sociodem_coact" in [story["gameId"] for story in client['game_history']] and next(story for story in client['game_history'] if story["gameId"] == "sociodem_coact")['end_time']>(now-h24in_sec)]
sociodem_list_done7d  = [client for client in client_list if "sociodem_coact" in [story["gameId"] for story in client['game_history']] and next(story for story in client['game_history'] if story["gameId"] == "sociodem_coact")['end_time']>(now-d7in_sec )]
sociodem_list_done    = [client for client in client_list if "sociodem_coact" in [story["gameId"] for story in client['game_history']]]


# fill Participants amb problemes de salut mental
info_table.loc["Participants amb problemes de salut mental"] = [sum(1 for client in sociodem_list_done24h if client["pp"] == "Sí"),
                                          sum(1 for client in sociodem_list_done7d  if client["pp"] == "Sí"),
                                          sum(1 for client in sociodem_list_done    if client["pp"] == "Sí")]

# fill Cuidador
info_table.loc["Cuidador"] = [sum(1 for client in sociodem_list_done24h if client["p_cuid"] == "Sí"),
                                          sum(1 for client in sociodem_list_done7d  if client["p_cuid"] == "Sí"),
                                          sum(1 for client in sociodem_list_done    if client["p_cuid"] == "Sí")]

# fill neither amb problemes de salut mental nor Cuidador
info_table.loc["Ni primera persona ni cuidador (2x 'No')"] = [sum(1 for client in sociodem_list_done24h if client["p_cuid"] == "No" and client["pp"] == "No"),
                                                                         sum(1 for client in sociodem_list_done7d  if client["p_cuid"] == "No" and client["pp"] == "No"),
                                                                         sum(1 for client in sociodem_list_done     if client["p_cuid"] == "No" and client["pp"] == "No")]


info_table.loc["Ni primera persona ni cuidador (2x 'No' o 'nvr')"]  = [sum(1 for client in sociodem_list_done24h if client["p_cuid"] != "Sí" and client["pp"] != "Sí"),
                                                                          sum(1 for client in sociodem_list_done7d  if client["p_cuid"] != "Sí" and client["pp"] != "Sí"),
                                                                          sum(1 for client in sociodem_list_done     if client["p_cuid"] != "Sí" and client["pp"] != "Sí")]

info_table["total (%)*"] = info_table.total/num_soc*100.
decimals = 1
info_table["total (%)*"] = info_table["total (%)*"].apply(lambda x: round(x, decimals))
gen_stats_text += info_table.to_html()
gen_stats_text += "* la última columna indica, cuál porcentaje de los participantes que han respondido al sociodem han respondido que són A) primeras personas, B) Cuidadores, C) No Primeras personas + no cuidadores, D) No/nvr primeras personas, No/nvr cuidadores."

################# THIRD PART OF MAIL: more info ####################################

title = "<H3>Número de relatos respondidos</H3>"
gen_stats_text += title

def count_elements(seq) -> dict:
    """Tally elements from `seq`."""
    hist = {}
    for i in seq:
        hist[i] = hist.get(i, 0) + 1
    return hist

def ascii_histogram(seq) -> None:
    """A horizontal frequency-table/histogram plot."""
    counted = count_elements(seq)
    html_text = "<p>"
    for k in sorted(counted):
        html_text+='{0:5d} {1}'.format(k, '+' * counted[k])+"<br>"
    html_text += "</p>"
    return html_text

sub_title = "<H4>Cuantos relatos fueron respondidos por cuantos participantes en total</H4>"
gen_stats_text += sub_title

sub_sub_title = "<H5>Cualquier tipo de relato</H5>"
gen_stats_text += sub_sub_title

num_rel = [len(client['game_history']) for client in client_list]
fig = ascii_histogram(num_rel)
gen_stats_text += fig

sub_sub_title = "<H5>Relatos C</H5>"
gen_stats_text += sub_sub_title
list_of_story_ids_of_typeC = [game["_id"] for game in games_list if game["title"]=="compartir_vivencias"]
num_relC = [len([1 for game in client['game_history'] if game["gameId"] in list_of_story_ids_of_typeC]) for client in client_list]
fig = ascii_histogram(num_relC)
gen_stats_text += fig

sub_sub_title = "<H5>Relatos T</H5>"
gen_stats_text += sub_sub_title
list_of_story_ids_of_typeT = [game["_id"] for game in games_list if game["title"]=="encontrar_soluciones_juntos"]
num_relT = [len([1 for game in client['game_history'] if game["gameId"] in list_of_story_ids_of_typeT]) for client in client_list]
fig = ascii_histogram(num_relT)
gen_stats_text += fig

sub_sub_title = "<H5>Relatos terminados en los últimos 24h</H5>"
gen_stats_text += sub_sub_title
list_of_story_f24h_per_participant =  [ len([1 for game in client['game_history'] if game['end_time']>(now-h24in_sec)]) for client in client_list]
fig = ascii_histogram(list_of_story_f24h_per_participant)
gen_stats_text += fig

sub_sub_title = "<H5>Relatos terminados en los últimos 7d</H5>"
gen_stats_text += sub_sub_title
list_of_story_f7d_per_participant =  [ len([1 for game in client['game_history'] if game['end_time']>(now-d7in_sec)]) for client in client_list]
fig = ascii_histogram(list_of_story_f7d_per_participant)
gen_stats_text += fig


sub_title = "<H4>Participantes que tienen relatos pendientes</H4>"
gen_stats_text += sub_title
total   = len([1 for client in client_list if client["current_game"]!=None])
last24h = len([1 for client in client_list if client["current_game"]!=None and (now - client["current_game"]['start_time']) > h24in_sec])
last7d  = len([1 for client in client_list if client["current_game"]!=None and (now - client["current_game"]['start_time']) > d7in_sec])
gen_stats_text += "<p>"+str(total)+" de momento tienen un dialogo/relato pendiente, de ell@s "+str(last24h)+" ya por más de 24h y de estos "+str(last7d)+" por más de 7 días."

sub_title = "<H3>configuraciones del participante</H3>"
gen_stats_text += sub_title
freq = [client.get("freq", None) for client in client_list]
text ="frecuencias: "+ str(count_elements(freq))
gen_stats_text += text+"<br>"

lang = [client.get("language", None) for client in client_list]
text ="idiomas: "+ str(count_elements(lang))
gen_stats_text += text


gen_stats_text = "<pre>"+ gen_stats_text +"</pre>"

send_mail("CoAct chatbot daily monitoring mail", gen_stats_text)#, images_in_mail_body=[filename_table_with_stats], attachment_path_list=[filename_table_with_stats])
# output for cronjob
print("mail sent on : ", datetime.now())
