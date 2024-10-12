import os
import threading
import asyncio
import time
from bot.painter import painters
from bot.mineclaimer import mine_claimer
from bot.utils import night_sleep, Colors
from bot.notpx import NotPx
from telethon.sync import TelegramClient
import telebot
from datetime import datetime, timedelta
import sqlite3

# Global variable to store the bot instance and token expiration
bot_instances = {}
token_expiration = None
bot_token = None
lock = threading.Lock()

def get_bot_instance(token):
    global bot_token, token_expiration
    if bot_token is None or datetime.now() >= token_expiration:
        bot_token = token
        token_expiration = datetime.now() + timedelta(hours=2)
        print(f"[+] Your bot token is valid for 2 hours from now.")
    if token not in bot_instances:
        bot_instances[token] = telebot.TeleBot(token)
    return bot_instances[token]

async def run_mine_claimer(cli, session_name):
    await mine_claimer(cli, session_name)

async def run_painters(cli, session_name):
    await painters(cli, session_name)

def run_async_functions(cli, session_name):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(asyncio.gather(
            run_mine_claimer(cli, session_name),
            run_painters(cli, session_name)
        ))
    finally:
        loop.close()

def multithread_starter():
    global bot_token, token_expiration
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
                proxy = load_proxy(session_name)  # Load proxy for session
                print(f"[+] Loading session: {session_name}")
                if proxy:
                    print(f"[+] Using proxy: {proxy} for session {session_name}")
                else:
                    print(f"[!] No proxy found for session {session_name}. Running without proxy.")
                
                # Initialize NotPx without 'proxy' argument since it caused errors
                cli = NotPx(f"sessions/{session_name}")

                threading.Thread(target=run_async_functions, args=(cli, session_name)).start()
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

def reset_api_credentials():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env.txt')
    if os.path.exists(env_path):
        os.remove(env_path)
        print("[+] API credentials reset successfully.")
    else:
        print("[!] No env.txt file found. Nothing to reset.")

def reset_proxy():
    proxy_file = "proxy_list.txt"
    if os.path.exists(proxy_file):
        os.remove(proxy_file)
        print("[+] Proxy list reset successfully.")
    else:
        print("[!] No proxy file found. Nothing to reset.")

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

def add_proxy():
    proxy = input("Enter proxy (format: host:port or username:password@host:port): ")
    session_name = input("Enter session name to assign this proxy to: ")
    proxy_file = "proxy_list.txt"
    with open(proxy_file, "a") as f:
        f.write(f"{session_name}={proxy}\n")
    print(f"[+] Proxy {proxy} added to session {session_name}.")

def load_proxy(session_name):
    proxy_file = "proxy_list.txt"
    if os.path.exists(proxy_file):
        with open(proxy_file, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith(f"{session_name}="):
                    return line.split('=')[1].strip()
    return None

def process():
    global bot_token
    print(r"""  
        ███╗   ███╗  ██████╗  ██╗  ██╗ ███████╗ ██╗ ███╗   ██╗
        ████╗ ████║ ██╔═══██╗ ██║  ██║ ██╔════╝ ██║ ████╗  ██║
        ██╔████╔██║ ██║   ██║ ███████║ ███████╗ ██║ ██╔██╗ ██║
        ██║╚██╔╝██║ ██║   ██║ ██╔══██║ ╚════██║ ██║ ██║╚██╗██║
        ██║ ╚═╝ ██║ ╚██████╔╝ ██║  ██║ ███████║ ██║ ██║ ╚████║
        ╚═╝     ╚═╝  ╚═════╝  ╚═╝  ╚═╝ ╚══════╝ ╚═╝ ╚═╝  ╚═══╝
                                                
        NotPx Auto Paint & Claim by @helpppeeerrrrrr - v1.0 {}""".format(Colors.BLUE, Colors.END))
    
    print("Starting Telegram bot...")
    bot_token = input("Enter your bot token: ")
    bot = get_bot_instance(bot_token)
    
    # Start bot polling in a separate thread
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
        print("8. Exit")

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
                    print(f"[+] Session {name} saved successfully.")
                else:
                    print("[!] API credentials not found. Please add them first.")
            else:
                print(f"[x] Session {name} already exists.")
        elif option == "2":
            multithread_starter()
        elif option == "3":
            add_api_credentials()
        elif option == "4":
            reset_api_credentials()
        elif option == "5":
            reset_session()
        elif option == "6":
            add_proxy()
        elif option == "7":
            reset_proxy()
        elif option == "8":
            print("Exiting...")
            bot.stop_polling()
            bot_thread.join()
            break
        else:
            print("[!] Invalid option. Please try again.")

if __name__ == "__main__":
    if not os.path.exists("sessions"):
        os.mkdir("sessions")
    process()
