import os
import threading
import asyncio
import time
import requests
import json
from bot.painter import painters
from bot.mineclaimer import mine_claimer
from bot.utils import night_sleep, Colors
from bot.notpx import NotPx
from telethon.sync import TelegramClient
import telebot
from datetime import datetime, timedelta
import sqlite3

# Global variables
bot_instances = {}
lock = threading.Lock()
token_expiration = None  # To store the token expiration time
valid_bot_token = None  # To store the valid bot token

# To store proxies
proxies = {}

def get_bot_instance(bot_token):
    global valid_bot_token, token_expiration
    if bot_token not in bot_instances:
        bot_instances[bot_token] = telebot.TeleBot(bot_token)
    return bot_instances[bot_token]

async def run_mine_claimer(cli, session_name):
    await mine_claimer(cli, session_name)

async def run_painters(cli, session_name):
    await painters(cli, session_name)

def run_async_functions(cli, session_name, proxy):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(asyncio.gather(
            run_mine_claimer(cli, session_name),
            run_painters(cli, session_name)
        ))
    finally:
        loop.close()

def multithread_starter(bot_token):
    print("Starting the mining and claiming process...")

    if not os.path.exists("sessions"):
        os.mkdir("sessions")

    dirs = os.listdir("sessions/")
    sessions = list(filter(lambda x: x.endswith(".session"), dirs))
    sessions = list(map(lambda x: x.split(".session")[0], sessions))

    if not sessions:
        print("[!] No sessions found.")
        return

    for session_name in sessions:
        try:
            with lock:
                print(f"[+] Loading session: {session_name}")
                cli = NotPx("sessions/" + session_name)

                proxy = proxies.get(session_name)
                if proxy:
                    print(f"[+] Using proxy: {proxy} for {session_name}")
                else:
                    print(f"[!] No proxy found for session {session_name}, running without proxy.")

                threading.Thread(target=run_async_functions, args=(cli, session_name, proxy)).start()
        except Exception as e:
            print(f"[!] Error on load session \"{session_name}\", error: {e}")

def add_api_credentials():
    api_id = input("Enter API ID: ")
    api_hash = input("Enter API Hash: ")
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env.txt')
    with open(env_path, "w") as f:
        f.write(f"API_ID={api_id}\n")
        f.write(f"API_HASH={api_hash}\n")
    print("[+] API credentials saved successfully in env.txt file.")

def add_proxy():
    session_name = input("Enter the session name for proxy: ")
    proxy = input("Enter proxy (format: http://username:password@ip:port): ")

    # Validate the proxy format
    if not proxy.startswith("http://") or not proxy.count(":") == 3:
        print("[!] Invalid proxy format. Please use http://username:password@ip:port format.")
        return

    proxies[session_name] = proxy
    print(f"[+] Proxy {proxy} added for {session_name}.")

def reset_proxy():
    session_name = input("Enter the session name to reset proxy: ")
    if session_name in proxies:
        del proxies[session_name]
        print(f"[+] Proxy reset for {session_name}.")
    else:
        print(f"[!] No proxy found for {session_name}.")

def reset_api_credentials():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env.txt')
    if os.path.exists(env_path):
        os.remove(env_path)
        print("[+] API credentials reset successfully.")
    else:
        print("[!] No env.txt file found. Nothing to reset.")

def load_api_credentials():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env.txt')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
            api_id = None
            api_hash = None
            for line in lines:
                if line.startswith('API_ID='):
                    api_id = line.split('=')[1].strip()
                elif line.startswith('API_HASH='):
                    api_hash = line.split('=')[1].strip()
            return api_id, api_hash
    return None, None

def save_session(name):
    with open("sessions/sessions_list.txt", "a") as f:
        f.write(name + "\n")

def load_sessions():
    if not os.path.exists("sessions/sessions_list.txt"):
        return []
    with open("sessions/sessions_list.txt", "r") as f:
        return [line.strip() for line in f.readlines()]

def show_sessions():
    sessions = load_sessions()
    if sessions:
        print("[+] Active Sessions:")
        for session in sessions:
            print(f"  - {session}")
    else:
        print("[!] No active sessions found.")

def process():
    global token_expiration, valid_bot_token

    print(r"""  
        ███╗   ███╗  ██████╗  ██╗  ██╗ ███████╗ ██╗ ███╗   ██╗
        ████╗ ████║ ██╔═══██╗ ██║  ██║ ██╔════╝ ██║ ████╗  ██║
        ██╔████╔██║ ██║   ██║ ███████║ ███████╗ ██║ ██╔██╗ ██║
        ██║╚██╔╝██║ ██║   ██║ ██╔══██║ ╚════██║ ██║ ██║╚██╗██║
        ██║ ╚═╝ ██║ ╚██████╔╝ ██║  ██║ ███████║ ██║ ██║ ╚████║
        ╚═╝     ╚═╝  ╚═════╝  ╚═╝  ╚═╝ ╚══════╝ ╚═╝ ╚═╝  ╚═══╝
                                                
        NotPx Auto Paint & Claim by @helpppeeerrrrrr - v1.0 {}""".format(Colors.BLUE, Colors.END))
    
    if valid_bot_token is None or datetime.now() >= token_expiration:
        bot_token = input("Enter your bot token: ")
        valid_bot_token = bot_token
        token_expiration = datetime.now() + timedelta(hours=2)
        print(f"[+] Your bot token is valid for 2 hours from now.")
    else:
        print(f"[+] Using cached bot token. It is valid until {token_expiration}.")
    
    bot = get_bot_instance(valid_bot_token)  # Get the bot instance with the valid token
    
    bot_thread = threading.Thread(target=bot.polling, kwargs={"none_stop": True})
    bot_thread.start()
    
    while True:
        print("\nMain Menu:")
        print("1. Add Account session")
        print("2. Start Mine + Claim")
        print("3. Add API ID and Hash")
        print("4. Reset API Credentials")
        print("5. Reset Session")
        print("6. Add Proxy")
        print("7. Reset Proxy")
        print("8. Show Active Sessions")  # New option for showing sessions
        print("9. Exit")
        
        option = input("Enter your choice: ")
        
        if option == "1":
            name = input("\nEnter Session name: ")
            if not os.path.exists("sessions"):
                os.mkdir("sessions")
            if not any(name in i for i in os.listdir("sessions/")):
                api_id, api_hash = load_api_credentials()
                if api_id and api_hash:
                    client = TelegramClient("sessions/" + name, api_id, api_hash).start()
                    client.disconnect()
                    save_session(name)
                    print("[+] Session {} {}saved successfully{}.".format(name, Colors.GREEN, Colors.END))
                else:
                    print("[!] API credentials not found. Please add them first.")
            else:
                print("[x] Session {} {}already exists{}.".format(name, Colors.RED, Colors.END))
        elif option == "2":
            multithread_starter(valid_bot_token)  # Pass the valid bot token
        elif option == "3":
            add_api_credentials()
        elif option == "4":
            reset_api_credentials()
        elif option == "5":
            reset_session()
        elif option == "6":
            add_proxy()  # Calls the function to add a proxy
        elif option == "7":
            reset_proxy()
        elif option == "8":
            show_sessions()  # Call the function to show active sessions
        elif option == "9":
            print("Exiting...")
            bot.stop_polling()
            bot_thread.join()
            break
        else:
            print("[!] Invalid option. Please try again.")

if __name__ == "__main__":
    if not os.path.exists("sessions"):
        os.mkdir("sessions")
    load_sessions()  # Load existing sessions
    process()
