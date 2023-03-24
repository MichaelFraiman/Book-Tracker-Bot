import json
import telebot
from telebot import types
import re
from pathlib import Path
import hashlib
import base64
import os
import datetime


with open("private/token.txt") as f:
    TOKEN = re.sub(r'\s', "", f.read())

bot = telebot.TeleBot(TOKEN)

def set_filename(message):
    
    id = str(message.chat.id)
    
    my_bytes = id.encode('utf-8')
    my_hash = hashlib.sha512(my_bytes).digest()
    my_base32_hash = base64.b32encode(my_hash).decode('utf-8')
    
    s = os.path.join("jsons", "books_" + my_base32_hash[:20] + ".json")
    return s

# Reads a json file
def json_read(filename):
    try:
        with open(filename, "r") as f:
            json_str = f.read()
            data = json.loads(json_str)
    except Exception as e:
        data = []
    
    return data

# Writes to a json file
def json_write(filename, contents):
    with open(filename, "w") as f:
        json.dump(contents, f, indent=2)

def create_file(filename):

    p = Path(filename)
    dirname = p.parent
    filename = p.name

    print(dirname)
    print(filename)

    Path(dirname).mkdir(parents=True, exist_ok=True)
    file_path = Path(os.path.join(dirname, filename))

    if not file_path.is_file():
        with open(file_path, "w") as f:
            pass

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    create_file(set_filename(message))
    bot.reply_to(message, "Hello, this bot tracks your book reding activity")
    menu_main(message)

# Function that posts main menu buttons
def menu_main(message):
    chat_id = message.chat.id
    button_list = ["Add a new book", "Start reading", "See statistics"]
    post_buttons(chat_id,button_list)

# Menu with a stop button
def menu_stop(message, name):
    chat_id = message.chat.id
    button_list = ["Stop"]
    # Add name to callback info
    post_buttons(chat_id,button_list,f"_action:stop_{name}_")

# Posts list of buttons
def post_buttons(chat_id, button_list, prepend=""):
    # Create a new inline keyboard with the specified list of buttons
    keyboard = types.InlineKeyboardMarkup()
    for button in button_list:
        keyboard.add(types.InlineKeyboardButton(text=button, callback_data= prepend + button))
    
    # Send the keyboard to the user
    bot.send_message(chat_id, "Please select an option:", reply_markup=keyboard)

# Returns a keyboard with list of books to post 
def book_list(books):
    keyboard = types.InlineKeyboardMarkup()
    for b in books:
        keyboard.add(types.InlineKeyboardButton(text=b, callback_data= "_book:name_" + b))

    return keyboard

# Returns list os names of the books
def book_get_list(message):
    data = json_read(set_filename(message))
    books_names = []
    for d in data:
        if 'author' in d:
            author = " [" + d['author'] + "]"
        else:
            author = ""
        books_names.append(d['name'] + author)

    return books_names

# returns an entry with book info
def book_info(name, filename):

    data = json_read(filename)

    for d in data:
        if d["name"] == name:
            return d
    
    return None

# turns json into a message for a user
def book_print_info(d):

    s = "Name: " + d["name"]

    if d["author"]:
        s += "\n" + "Author: " + d["author"]

    return s

# funtion to start reading a book
def read_start(name, filename):
    data = json_read(filename)
    for d in data:
        if d["name"] == name:
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime('%Y-%m-%d_%H:%M:%S.%f')
            if "page_stop" in d:
                page = d["page_stop"].split()[-1]
            else:
                page = 1
            if "time_start" in d:
                d["time_start"] += " " + str(formatted_time)
                d["page_start"] += " " + str(page)
            else:
                d["time_start"] = str(formatted_time)
                d["page_start"] = str(page)
            
            break

    json_write(filename, data)

    return data
    

def ask_page(message, name, filename):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please enter the page")
    bot.register_next_step_handler(message, lambda msg: read_stop(msg, name, filename))

def read_stop(message, name, filename):
    page = message.text
    data = json_read(filename)
    for d in data:
        if d["name"] == name:
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime('%Y-%m-%d_%H:%M:%S.%f')
            if "time_stop" in d:
                d["time_stop"] += " " + str(formatted_time)
                d["page_stop"] += " " + str(page)
            else:
                d["time_stop"] = str(formatted_time)
                d["page_stop"] = str(page)
        

            break

    json_write(filename, data)

    menu_main(message)


def info_start(message, filename):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please enter the name of the book")
    bot.register_next_step_handler(message, lambda msg: info_name(msg, filename))

def info_name(message, filename):
    chat_id = message.chat.id
    name = message.text
    #bot.send_message(chat_id, "You have entered the name " + name)
    bot.send_message(chat_id, "Please enter the author")
    bot.register_next_step_handler(message, lambda msg: info_author(msg, name, filename) )

def info_author(message, name, filename):
    chat_id = message.chat.id
    author = message.text
    #bot.send_message(chat_id, "You have entered the name " + name)
    #bot.send_message(chat_id, "You have entered the author " + author)
    data = json_read(filename)

    flag = False
    for d in data:
        if d["name"] == name:
            bot.send_message(chat_id, "This book already exists")
            flag = True
            break
    
    if flag == False:
        bot.send_message(chat_id, "Please enter the total number of pages")
        bot.register_next_step_handler(message, lambda msg: info_pages(msg, name, author, filename) )
    else:
        menu_main(message)

def info_pages(message, name, author, filename):
    data = json_read(filename)
    tot_pages = message.text
    chat_id = message.chat.id
    try:
        p = int(tot_pages)
        d = {
            "name": name,
            "author": author,
            "page_total": tot_pages
        }
        data.append(d)
        json_write(filename, data)
        menu_main(message)
    except:
        bot.send_message(chat_id, "The page should be an integer, try again")
        bot.register_next_step_handler(message, lambda msg: info_pages(msg, name, author, filename) )


# calculates total time spent
def calc_time(start, stop):
    time_format = '%Y-%m-%d_%H:%M:%S.%f'
    s = start.split()
    f = stop.split()

    tot = datetime.timedelta()

    for i, t in enumerate(s):
        time1 = datetime.datetime.strptime(s[i], time_format)
        time2 = datetime.datetime.strptime(f[i], time_format)
        delta = time2 -time1
        tot += delta

    return tot


# show total time of reading
def stats_show(message):
    chat_id = message.chat.id
    filename = set_filename(message)
    data = json_read(filename)

    s = "The total amount of time spent:"

    for d in data:
        if "time_start" in d:
            tot = calc_time(d["time_start"], d["time_stop"])
            page_cur = d["page_stop"].split()[-1]
            page_tot = d["page_total"]
            formatted = re.sub(r"\:\d\d\.\d+$", "", str(tot))
            s += "\n" + d["name"] + f" [by {d['author']}] " + formatted + f". Page {page_cur}/{page_tot}"
        else:
            s += "\n" + d["name"] + f" [by {d['author']}] " + "NEW"
    
    bot.send_message(chat_id, s)

# Handler for callback queries
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.message:
        # Execute a function based on the button that the user pressed
        chat_id = call.message.chat.id
        match call.data:
            case "Add a new book":
                info_start(call.message, set_filename(call.message))
                #menu_main(call.message)
            case "Start reading":
                bot.send_message(chat_id, "List of current books:")
                books_list = book_get_list(call.message)
                if books_list != []:
                    keyboard = book_list(books_list)                    
                    bot.send_message(chat_id, "Please select a book:", reply_markup=keyboard)
                else:
                    bot.send_message(chat_id, "There are no books yet")
                    menu_main(call.message)
            case "See statistics":
                #bot.send_message(chat_id, "Not implemented yet")
                stats_show(call.message)
                menu_main(call.message)
            case _:
                # Callback is a book name
                if str(call.data).startswith("_book:name_"):
                    name = re.sub("_book:name_", "", call.data)
                    name = re.sub(r"\s\[.*\]$","",name)
                    d = book_info(name, set_filename(call.message))
                    if d != None:
                        s = book_print_info(d)
                        bot.send_message(chat_id, s)
                        read_start(name, set_filename(call.message))
                        menu_stop(call.message, name)
                        #menu_main(call.message)
                elif str(call.data).startswith("_action:stop_"):
                    name = re.sub("_action:stop_", "", call.data)
                    name = re.sub("_Stop", "", name)
                    ask_page(call.message, name, set_filename(call.message))
                else: 
                    menu_main(call.message)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
   menu_main(message)

def main():
    
    Path("jsons").mkdir(parents=True, exist_ok=True)

    bot.polling()

    return



main()