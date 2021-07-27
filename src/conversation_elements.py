"""
A collection of random or deterministic 
conversation elements like random positive smileys
or random greetings and goodbyes to make the conversation less stiff
or short informative texts that need translations into the 4 languages
"""

import html
import random 

######### SMILEY COLLECTIONS ##################################################
smileys = {"positive":["\N{thumbs up sign}",
                    "\N{smiling face with smiling eyes}"],
            "sad"    :["\N{pensive face}"]}

time_is_over = {"ca": "Temps d'espera esgotat.", 
                "es": "Tiempo de espera agotado.", 
                "en": "Timeout.", 
                "de": "Wartezeit abgelaufen."
                }

you_are_unsubscribed = { "ca":'Has posat en pausa el xatbot. Recorda que si escrius REPRENDRE pots tornar a rebre missatges.', 
                         "es":'Has puesto en pausa el chatbot. Recuerda que si escribes REANUDAR puedes volver a recibir mensajes.',
                         "en":'You paused the chatbot. Remember that if you type RESUME you can receive messages again.',
                         "de":'Der Chatbot pausiert. Wenn du FORTSETZEN schreibst, kannst du wieder Nachrichten erhalten.'
                        }

unsufficient_players = {"ca":'No hi ha prou participants per a la interacció.', 
                        "es":'No hay suficientes participantes para la interacción.' ,
                        "en":'There aren’t enough participants for this interaction.' ,
                        "de":'Es gibt gerade nicht genug Teilnehmer für die Interaktion.'}

default_answer_msg = {   'ca': "Aquest xatbot només permet respondre a través de botons. El xatbot no és un servei d'ajuda psicològica professional, és una eina de recerca científica participativa. Si necessites suport psicològic, demana ajuda i adreça’t al teu servei de salut de referència www.salutmental.org/coact-ajuda-ayuda-help-hilfe.\n\n\nPotser voldries ajustar les  configuracions del xatbot?\n\n/lang per configurar l’idioma\n/freq per modificar la freqüència dels relats\n/pausar per deixar de rebre continguts\n/reprendre per tornar a rebre continguts\n/baixa per donar-te de baixa",
                         'es': 'Este chatbot sólo permite responder a través de botones. El chatbot no es un servicio de ayuda psicológica profesional, es una herramienta de investigación científica participativa. Si necesitas apoyo psicológico, pide ayuda y dirígete a tu servicio de salud de referencia www.salutmental.org/coact-ajuda-ayuda-help-hilfe.\n\n\nQuizás quieres ajustar las configuraciones del chatbot?\n\n/lang para configurar el idioma\n/freq para modificar la frecuencia de los relatos\n/pausar para dejar de recibir contenidos\n/reanudar para volver a recibir contenidos\n/baja para darte de baja',
                         'en': 'This chatbot only allows you to answer via buttons. The chatbot is not a professional psychological support service, it is a participatory research tool. If you need psychological support, ask for help and contact your referral health service www.salutmental.org/coact-ajuda-ayuda-help-hilfe.\n\n\nMaybe you want to adjust the chatbot settings?\n\n/lang to set the language\n/freq to change the stories’ frequency\n/pause to stop receiving content\n/resume to receive content again\n/unsubscribe to unsubscribe\n',
                         "de": "Dieser Chatbot interagiert nur über anklickbare Auswahlmöglichkeiten. Der Chatbot ist kein professioneller psychologischer Hilfsdienst, er ist ein Werkzeug zur partizipativen wissenschaftlichen Forschung. Wenn du psychologische Unterstützung benötigst, bitte um Hilfe und kontaktiere deinen lokalen Gesundheitsdienst www.salutmental.org/coact-ajuda-ayuda-help-hilfe.\n\n\nVielleicht willst du Einstellungen am Chatbot ändern?\n\n/lang um die Sprache einzustellen\n/freq um die Frequenz der Erzählungen zu ändern\n/pausieren um keine weiteren Inhalte zu bekommen\n/fortsetzen um wieder Inhalte zu erhalten\n/abmelden um dich abzumelden"
                         }

""" komplette version:
default_answer_msg = {   'ca': "Aquest xatbot només permet respondre a través de botons. El xatbot no és un servei d'ajuda psicològica professional, és una eina de recerca científica participativa. Si necessites suport psicològic, demana ajuda i adreça’t al teu servei de salut de referència www.salutmental.org/coact-ajuda-ayuda-help-hilfe.\n\n\nPotser voldries ajustar les  configuracions del xatbot?\n\n/lang per configurar l’idioma\n/freq per modificar la freqüència dels relats\n/day per triar el millor moment del dia per respondre els relats\n/world per ajustar la zona horària fus horari\n/pausar per deixar de rebre continguts\n/reprendre per tornar a rebre continguts\n/baixa per donar-te de baixa",
                         'es': 'Este chatbot sólo permite responder a través de botones. El chatbot no es un servicio de ayuda psicológica profesional, es una herramienta de investigación científica participativa. Si necesitas apoyo psicológico, pide ayuda y dirígete a tu servicio de salud de referencia www.salutmental.org/coact-ajuda-ayuda-help-hilfe.\n\n\nQuizás quieres ajustar las configuraciones del chatbot?\n\n/lang para configurar el idioma\n/freq para modificar la frecuencia de los relatos\n/day para elegir el mejor momento del día para responder los relatos\n/world para ajustar la zona horaria zona horaria\n/pausar para dejar de recibir contenidos\n/reanudar para volver a recibir contenidos\n/baja para darte de baja',
                         'en': 'This chatbot only allows you to answer via buttons. The chatbot is not a professional psychological support service, it is a participatory research tool. If you need psychological support, ask for help and contact your referral health service www.salutmental.org/coact-ajuda-ayuda-help-hilfe.\n\n\nMaybe you want to adjust the chatbot settings?\n\n/lang to set the language\n/freq to change the stories’ frequency\n/day to choose the best time of day to answer the stories\n/world to adjust the time zone\n/pause to stop receiving content\n/resume to receive content again\n/unsubscribe to unsubscribe\n',
                         "de": "Dieser Chatbot interagiert nur über anklickbare Auswahlmöglichkeiten. Der Chatbot ist kein professioneller psychologischer Hilfsdienst, er ist ein Werkzeug zur partizipativen wissenschaftlichen Forschung. Wenn du psychologische Unterstützung benötigst, bitte um Hilfe und kontaktiere deinen lokalen Gesundheitsdienst www.salutmental.org/coact-ajuda-ayuda-help-hilfe.\n\n\nVielleicht willst du Einstellungen am Chatbot ändern?\n\n/lang um die Sprache einzustellen\n/freq um die Frequenz der Erzählungen zu ändern\n/day um die Tageszeit einzustellen\n/world um die Zeitzone anzupassen\n/pausieren um keine weiteren Inhalte zu bekommen\n/fortsetzen um wieder Inhalte zu erhalten\n/abmelden um dich abzumelden"
                         }
"""

wrong_answer = {
                'ca': 'Hauries de clicar en algun dels botons, si us plau.',#Les dades introduïdes no són correctes.',
                'es': 'Deberías clicar en alguno de los botones, por favor.',#,Los datos introducidos no son correctos.
                'en': 'Please click one of the buttons.',#The data entered is incorrect.',
                "de": "Bitte klicke eine der Möglichkeiten an."#Die eingegebenen Daten sind nicht korrekt."
                }

command_other_than_baixa_o_pausa_during_dialogue = {
                'ca': 'La petició que has escrit només pot ser utilitzada un cop acabem el diàleg que estem mantenint en aquest moment.',
                'es': 'La petición que has escrito solo puede ser utilizado una vez finalicemos el diálogo que estamos manteniendo en este momento.',
                'en': 'The command you’ve typed can only be used once this current dialogue is over.',
                "de": 'Die Anweisung, die du geschrieben hast, kann erst genutzt werden, wenn der derzeit laufende Dialog beendet ist.'
                }

def random_charged_emoji_html(charge = "positive"):
    """
    chose random emoji with a charge out of the smileys keys
    make html readable
    """
    # pick random emoji out of charged list
    smiley = random.choice(smileys[charge])
    # make html readable
    smiley = html.unescape(smiley)
    return smiley
