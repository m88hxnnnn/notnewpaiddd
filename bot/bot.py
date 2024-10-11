import os
import threading
import asyncio
import logging  # Added for logging
from bot.painter import painters
from bot.mineclaimer import mine_claimer
from bot.utils import Colors
from bot.notpx import NotPx
from telethon.sync import TelegramClient
import telebot
from datetime import datetime, timedelta

# Function to prompt and save the bot token
def set_bot_token():
    token = input("Enter your Bot Token: ")
    os.environ["BOT_TOKEN"] = token
    return token

# Load the bot token from an environment variable or ask for it
BOT_TOKEN = os.getenv("BOT_TOKEN") or set_bot_token()

if not BOT_TOKEN:
    raise ValueError("Bot token not found. Set it as an environment variable or input it when prompted.")

bot = telebot.TeleBot(BOT_TOKEN)
bot_thread = None  # Global reference to bot polling thread for proper stopping

# Setup a logger for each session
def setup_logger(session_name):
    logger = logging.getLogger(session_name)
    logger.setLevel(logging.INFO)

    # Create a file handler for the log file
    log_file = os.path.join("logs", f"{session_name}.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = logging.FileHandler(log_file)

    # Create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(file_handler)
    return logger

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

def multithread_starter():
    if not os.path.exists("sessions"):
        os.mkdir("sessions")
    dirs = os.listdir("sessions/")
    sessions = list(filter(lambda x: x.endswith(".session"), dirs))
    sessions = list(map(lambda x: x.split(".session")[0], sessions))
    
    for session_name in sessions:
        try:
            cli = NotPx("sessions/" + session_name)
            logger = setup_logger(session_name)  # Create a logger for each session

            def run_painters():
                logger.info("Started painters process")  # Log starting of process
                asyncio.run(painters(cli, session_name))

            def run_mine_claimer():
                logger.info("Started mine claimer process")  # Log starting of process
                asyncio.run(mine_claimer(cli, session_name))

            threading.Thread(target=run_painters).start()
            threading.Thread(target=run_mine_claimer).start()
            logger.info("Started both threads for session: {}".format(session_name))
        except Exception as e:
            logger.error("Error on load session {}: {}".format(session_name, e))
            print("[!] {}Error on load session{} \"{}\", error: {}".format(Colors.RED, Colors.END, session_name, e))

def start_bot_polling():
    global bot_thread
    if not bot_thread or not bot_thread.is_alive():
        print("Starting Telegram bot polling...")
        bot_thread = threading.Thread(target=bot.polling, kwargs={"none_stop": True})
        bot_thread.start()

def stop_bot_polling():
    global bot_thread
    if bot_thread and bot_thread.is_alive():
        print("Stopping Telegram bot polling...")
        bot.stop_polling()
        bot_thread.join()  # Ensure the thread is stopped properly

def process():
    print(r"""{}
███████  █████  ██    ██  █████  ███    ██ 
██      ██   ██ ██    ██ ██   ██ ████   ██ 
███████ ███████ ██    ██ ███████ ██ ██  ██ 
     ██ ██   ██  ██  ██  ██   ██ ██  ██ ██ 
███████ ██   ██   ████   ██   ██ ██   ████ 
                                                
            NotPx Auto Paint & Claim by @sgr - v1.0 {}""".format(Colors.BLUE, Colors.END))
    
    start_bot_polling()  # Start polling at the beginning
    
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
                    print("[+] Session {} {}saved success{}.".format(name, Colors.GREEN, Colors.END))
                else:
                    print("[!] API credentials not found. Please add them first.")
            else:
                print("[x] Session {} {}already exist{}.".format(name, Colors.RED, Colors.END))
        elif option == "2":
            multithread_starter()
        elif option == "3":
            add_api_credentials()
        elif option == "4":
            reset_api_credentials()
        elif option == "5":
            reset_session()
        elif option == "6":
            print("Exiting...")
            stop_bot_polling()  # Stop polling on exit
            break
        else:
            print("[!] Invalid option. Please try again.")

if __name__ == "__main__":
    if not os.path.exists("sessions"):
        os.mkdir("sessions")
    process()
