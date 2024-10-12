import os
import threading
import asyncio
import time
import uuid
import requests
import json
from bot.painter import painters
from bot.mineclaimer import mine_claimer
from bot.utils import night_sleep, Colors
from bot.notpx import NotPx
from telethon.sync import TelegramClient
import telebot
from datetime import datetime
import sqlite3

# Global variable to store the bot instance
bot_instances = {}
lock = threading.Lock()

def get_bot_instance(bot_token):
    if bot_token not in bot_instances:
        bot_instances[bot_token] = telebot.TeleBot(bot_token)
    return bot_instances[bot_token]

async def run_mine_claimer(cli, session_name):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            await mine_claimer(cli, session_name)
        else:
            asyncio.run(mine_claimer(cli, session_name))
    except RuntimeError:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(mine_claimer(cli, session_name))

async def run_painters(cli, session_name):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            await painters(cli, session_name)
        else:
            asyncio.run(painters(cli, session_name))
    except RuntimeError:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(painters(cli, session_name))

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

                def painters_thread():
                    print(f"[+] Starting painters for session: {session_name}")
                    asyncio.run(run_painters(cli, session_name))
                    print(f"[+] Painters finished for session: {session_name}")

                def mine_claimer_thread():
                    print(f"[+] Starting mine claimer for session: {session_name}")
                    asyncio.run(run_mine_claimer(cli, session_name))
                    print(f"[+] Mine claimer finished for session: {session_name}")

                threading.Thread(target=painters_thread).start()
                threading.Thread(target=mine_claimer_thread).start()
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

def reset_session():
    if not os.path.exists("sessions"):
        os.mkdir("sessions")
    sessions = [f for f in os.listdir("sessions/") if f.endswith(".session")]
    if not sessions:
        print("[!] No sessions found.")
        return
    print("Available sessions:")
    for i, session in enumerate(sessions, 1):
        print(f"{i}. {session[:-8]}")
    choice = input("Enter the number of the session to reset: ")
    try:
        session_to_reset = sessions[int(choice) - 1]
        os.remove(os.path.join("sessions", session_to_reset))
        print(f"[+] Session {session_to_reset[:-8]} reset successfully.")
    except (ValueError, IndexError):
        print("[!] Invalid choice. Please try again.")

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

def process():
    print(r"""  
        ███╗   ███╗  ██████╗  ██╗  ██╗ ███████╗ ██╗ ███╗   ██╗
        ████╗ ████║ ██╔═══██╗ ██║  ██║ ██╔════╝ ██║ ████╗  ██║
        ██╔████╔██║ ██║   ██║ ███████║ ███████╗ ██║ ██╔██╗ ██║
        ██║╚██╔╝██║ ██║   ██║ ██╔══██║ ╚════██║ ██║ ██║╚██╗██║
        ██║ ╚═╝ ██║ ╚██████╔╝ ██║  ██║ ███████║ ██║ ██║ ╚████║
        ╚═╝     ╚═╝  ╚═════╝  ╚═╝  ╚═╝ ╚══════╝ ╚═╝ ╚═╝  ╚═══╝
        
                                                
            NotPx Auto Paint & Claim by @helpppeeerrrr - v1.0 {}""".format(Colors.BLUE, Colors.END))
    
    print("Starting Telegram bot...")
    bot_token = input("Enter your bot token: ")
    bot = get_bot_instance(bot_token)  # Get the bot instance with the provided token
    
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
        print("6. Exit")
        
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
                    save_session(name)  # Save session name to file
                    print("[+] Session {} {}saved successfully{}.".format(name, Colors.GREEN, Colors.END))
                else:
                    print("[!] API credentials not found. Please add them first.")
            else:
                print("[x] Session {} {}already exists{}.".format(name, Colors.RED, Colors.END))
        elif option == "2":
            multithread_starter(bot_token)  # Pass the bot token here
        elif option == "3":
            add_api_credentials()
        elif option == "4":
            reset_api_credentials()
        elif option == "5":
            reset_session()
        elif option == "6":
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
