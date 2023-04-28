# CoActuem per la Salut Mental Telegram Bot

CoActuem per la Salut Mental is part of the CoAct citizen social science project, funded by the European Union´s Horizon 2020 research and innovation programme under grant agreement number 873048.
CoActuem per la Salut Mental strives for a deeper understanding of social support networks in mental health. Central digital tool of this project is this Telegram chatbot. 
The chatbot manages several thousand one-to-one conversations within Telegram. It sends content in form of dialogues to the participants. The participants answer by pressing buttons. Content and design of the chatbot where created in a participatory co-creative process with around 30 co-researchers. The CoActuem per la Salut Mental chatbot runs on a Debian GNU/Linux 10 (buster) virtual machine. 
Anybody can join the running experiment by entering a conversation with the chatbot "CoActuem per la Salut Mental" in the Telegram app, available in English, Catalan, Spanish, and German. See also https://coactuem.ub.edu/ for a detailed description of the project and https://coactuem.ub.edu/pages/xat?locale=en to learn how to enter in conversation with the chatbot. 

The presented code allows to run the chatbot as was done within CoAct. To adapt the code to a different project, we recommend first trying to get the chatbot running in this present version, and only then make the adaptations to the new project, see "Adaptation for other projects" of this README. 

## How to run the chatbot

### Prerequisites: Installed Sofware, Telegram API, database setup

#### Installed Software

The chatbot is designed for Unix machines. The most essential you need to install:  
+ mongodb  
+ python3   
+ python3-telepot  
+ python3-pymongo  

For more specific requirements for both running the bot and plotting, see `./requirements.txt`

#### Telegram API https port

The bot communicates over https and thus needs TPC port 443 open (standard setup).

#### Telegram API and security

To run your own bot, you first need to create a TOKEN with which you can then access a HTTP API. Enter Telegram, search for "BotFather" among new contacts, and type `/newbot`. 

The TOKENs that you need to run a chatbot should be stored in an encrypted file `./tokens.json` together with a deencryption python code `./security/decrypt_files.py` stored in folder `./security` by a function called `decrypt` that needs the key stored in `./security/keys/` and returns the Telegram TOKEN for a given bot identifier. This code and the functions are called by `./src/settings.py`, so the TOKEN might as well be inserted there directly, if security doesn't play a role. The encrypted files with our TOKENs are of course not synced to git.  

To activate the security setup we propose, do:

1. Generate a Telegram Bot-API TOKEN by writing /newbot to bot "BotFather" inside the Telegram App and following the instructions.
2. Copy this TOKEN as in a json format into `./token.json` like this:

    {"my_bot_dev":"6078974884:AAzuk5123v7ujhekyx7q6YLzD9PtBGtT3zE",
     "my_bot":"6075908884:AAEGXL0vpPvjzgvztwydviwYLzD9PtBGtT3zE"}
     
3. From within `./security`, run first `python3 generate_keys.py` and then `python3 encrypt_files.py`.

After these three steps, `./src/settings.py` has all the parameters it needs to access data base and Telegram bot API.

#### Set up mongodb Database
To be able to run the bot in both developer and run mode, create two databases called `experiment_db_dev` and `experiment_db`, respectively, e.g. by running `./manipulate_db/create_empty_db.py` for each database name. 

The bot either sends fixed dialogues, stored in `./data/gamesInfo/` or short interaction snippets stored in `./src/conversation_elements.py`. The fixed dialogues follow a very rigid structure, see the `.json` files in `./data/gamesInfo/`, and can be uploaded to the mongo db via `./data/gamesInfo/update_mongoDB_games.py`. Any images or pdfs that you might want to send together with a dialogue need to be stored in `./data/gamesInfo/outgoing_files/`.

The chatbot sends the dialogues in the same fixed sequence to each participant. This sequence need to be stored in `./bot/sequence.txt` and then uploaded to the database via `./data/bot/read_names_relatos_and_add_list_to_bot_in_mongoDB.py`.

The database contains a collection called `hashes`. We do not disclose our hashing algorithm, but you can implement your own in `./src/hash_unhash.py`. This way of storing the participants data and their Telegram ID allows to neatly delete all private data (i.e. the Telegram ID, by deleting the hashes collection), while keeping all results from the experiment. 

### Run the chatbot

To start the chatbot on a Linux machine, type:  
    `nohup python3 -u main.py 2>> log/errorOutput.log >> log/output.log &`
or just:  
    `python3 main.py`

Also, there is a developer mode that can be customized as wished (currently it sends a message with the name of each dialogue to al users via Telegram before the dialogue starts, removes the waiting time between messages, and make non-rerunnable dialogues rerunnable):  
    `python3 main.py --dev`

## Chatbot and Database Monitoring and Logging

The main monitoring scripts can be setup as cronjobs. 

### Cronjobs
We use the following setup: 

The bash script `check_whether_bot_running` monitors the sustained performance of the chatbot. To activate it, first make it executable with command line prompt `chmod +x check_whether_bot_running` and then add the following line to your crontab (adapting `~/botcode/CoActuem_Telegram_bot/` to where the central `main.py` of the chatbot is stored on your device):  
    `\### bot monitoring: check every 5 minutes, whether bot is running, otherwise restart`
    `*/5 * * * * ~/botcode/CoActuem_Telegram_bot/check_whether_bot_running >> ~/botcode/CoActuem_Telegram_bot/log/bot_run_log_cron.log 2>&1`


To daily inform your mates via mail on the current status of the database (such as number and progress of participants):  
    `\### to send daily mail database status`
    `0 22 * * * ~/botcode/CoActuem_Telegram_bot/monitoring/general_daily.py  >> ~/botcode/CoActuem_Telegram_bot/monitoring/daily_mail_cron.out 2>&1`

To weekly give your team somewhat deeper insights on the participants distribution also via mail:  
    `### weekly mail database status with plots`
    `0 10 * * 1 ~/botcode/CoActuem_Telegram_bot/monitoring/general_weekly.py  >> ~/botcode/CoActuem_Telegram_bot/monitoring/weekly_mail_cron.out 2>&1`
    
Note that you need to make all cronjob scripts executable by runnning, e.g., `chmod +x general_weekly.py` in the according folder. 

Note further, that the SMTP setup for all three monitoring mail alerts has parameters apt for Microsoft outlook. To switch to a different mail provider, the line 

    `s = smtplib.SMTP(host='smtp-mail.outlook.com', port=587)`
    
needs to be adapted accordingly.

### Visualisations
The folder `./monitoring` contains several visualisation scripts that can then be attached to daily or weekly mails, to inform the team on the current state of the database.  
+ `plot_evolution_dialogues.py` plots the dialogue progress of all participants
+ `sankey_plot_from_db.py` module (called by general_weekly.py) that allows to visualize double profiles of participants, e.g. female, 65+ years old and professional in mental health.
+ `general_daily.py` and `general_weekly.py` read the current status of the database, especially the clients collection, and inform the team via mail
+ `minimal_mail.py` module for sending content and attachments to team; works for outlook, otherwise adapt SMTP server accordingly in the script
+ `keyring_entry.py` allows to hide the mail password

## Database Manipulations

You can manipulate the database in several ways, but the changes made will always only apply in the next run of the bot. The following database manipulation scripts are stored in `./manipulate_db` (make sure to always adapt the database name `experiment_db`; changes can not be undone.):

+ `change_status.py` to change whether certain users are active (and thus receive input) or not  
+ `clear_current_games.py` deletes the game/dialogue a user is currently answering (only on server side, not in the remote Telegram conversation)  
+ `clear_games_done.py` remove record of answered dialogues of a participant, so he/she can answer these dialogues again  
+ `create_empty_db.py` see above  
+ `print_db_status.py` see above  
+ `rm_user.py` cleanly remove all data of a participant from the database, e.g. when he/she decides to quit the experiment
    

## Runtime Interventions

The code itself is not interactive, meaning that once `main.py` is run, interventions other than abortion are not possible. 

### Admin Commands

To enable interventions during runtime, such as sending specific messages that are not within the fixed sequence, the chatbot promoters can change their own status to `admin` by typing `/admin` and the password to the chatbot. As admins they can then use the following commands within their conversation with the chatbot within Telegram:

+ `/global <name of game>` (sends game to all available users that did not already play it before)  
+ `/broadcast <message>` (sends message to all users (busy or waiting))  
+ `/status gives` some status info to the admin  
+ `/reload_users` loads user data from the clients collection of the database   
+ `/reload_games` loads game data from the gamesInfo collection of the database  
+ `/clear <id>` clears current games from user with `<id>`. If no id is given, all players are cleared  
+ `/set <game> <interval|pct|daytime>` allows to adapt dialogue timing and points, not used in our experiment. requires format <int|int|bool>  
+ `/save` save busy list and waiting list of users to bot database, e.g. before restarting the bot  
+ `/jugar <game>` send the specified dialogue to the admin  
+ `/msg <id> <messgae>` send message to user with id  

### User Commands

By typing any of the commands `pausar`, `pausar`, `pause`, `pausieren`, `/pausar`, `/pause`, `/pausieren` inside their conversation with the chatbot, the participants can pause the reception of new content (their status is set to 2). To afterwards carry on receiving content, the participants can use either of the commands `reprendre`, `reanudar`, `resume`, `fortsetzen`, `/reprendre`, `/reanudar`, `/resume`, `/fortsetzen`.   
With any of the commands `baixa`, `baja`, `unsubscribe`, `abmelden`, `/baixa`, `/baja`, `/unsubscribe`, or `/abmelden`, the participants can quit the experiment (their status is set to 3). They receive information on how they can additionally delete their entire data from the database.  
User commands `/freq` and `/lang` allows participant to adapt the inter-dialogue frequency and to adapt the language, respectively. Finally command `/delete_games_done` works only when the chatbot was run in developer mode: it clears the list of already answered dialogues of the participant who types it, to enable him/her to answer all dialogues again  

## Adaptation to other projects
To adapt this code package to your project, you need to addapt:

1) Generate the set of dialogues that you want to sent via the chatbot, by adding new `.json` files following the pattern of the `.json` files in `./data/gamesInfo/`. Note that the first field in the `.json` file, called `_id`, is the dialogue identifier as will be used in the mongo data base. For convenience, we give files and `_id`s exactly the same name. 
   
   Note: Files `hour.json`, `resume.json`, `welcome.json`, `lang.json`, `world.json`, `frequencia_relats.json`, `pause.json`, and  `unsubscribe.json` are imprescendible for the functioning of the chatbot. They don't form part of `sequence.txt`. Their texts can be adapted, but in case the button callback variables are changed, the correct functioning needs to be ensured by editing the source files in `./src/`, too.


2) Once the dialogues are prepared, they can be uploaded to the mongo data base by running `python3 update_mongoDB_games.py` from within the same folder `./data/gamesInfo/`.

3) Adapt the list of dialogues as sent to the participants: `./data/bot/sequence.txt`. It needs to contain the exact identifiers `_id`, one per row, without comma or empty spaces, just as presented in the example. This sequence is then activated by running `python3 read_names_relatos_and_add_list_to_bot_in_mongoDB.py` from within folder `.data/bot/`.

4) Add the files (mostly images and PDFs) that you want the chatbot to send along with the dialogues to folder `.data/outgoing_files/`, just as you reference them in the `.json` files in `./data/gamesInfo/`. 

5) In the context of Mental Health that requires a certain time of reflection. To limit the "playability" or "gamification" of the chatbot, we chose a relatively long pause of several seconds between consecutive messages that also depends on the length of the message about to be sent. Its duration can be adapted inside function  `calc_delay_sending` in `./src/telegram_bot.py`.





