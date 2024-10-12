import os
import threading
import asyncio
import logging
import fcntl  # For file locking
from bot.painter import painters
from bot.mineclaimer import mine_claimer
from bot.utils import Colors
from bot.notpx import NotPx
from telethon.sync import TelegramClient
import telebot
from datetime import datetime
import random
import platform
import time

# Function to clear the console
def clear_console():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

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

# Ensure unique session names to avoid conflicts
def generate_unique_session_name(base_name):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = str(random.randint(1000, 9999))
    return f"{base_name}_{timestamp}_{random_str}"

def add_api_credentials():
    api_id = input("Enter API ID: ")
    api_hash = input("Enter API Hash: ")
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env.txt')
    
    # File lock to ensure safe writing
    with open(env_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # Lock the file exclusively
        f.write(f"API_ID={api_id}\n")
        f.write(f"API_HASH={api_hash}\n")
        fcntl.flock(f, fcntl.LOCK_UN)  # Release the file lock

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
            fcntl.flock(f, fcntl.LOCK_SH)  # Shared lock for reading
            lines = f.readlines()
            api_id = None
            api_hash = None
            for line in lines:
                if line.startswith('API_ID='):
                    api_id = line.split('=')[1].strip()
                elif line.startswith('API_HASH='):
                    api_hash = line.split('=')[1].strip()
            fcntl.flock(f, fcntl.LOCK_UN)  # Release lock after reading
            return api_id, api_hash
    return None, None

async def run_painters(cli, session_name, logger):
    logger.info("Started painters process")
    try:
        await painters(cli, session_name)
    finally:
        await cli.disconnect()  # Ensure disconnecting the client

async def run_mine_claimer(cli, session_name, logger):
    logger.info("Started mine claimer process")
    try:
        await mine_claimer(cli, session_name)
    finally:
        await cli.disconnect()  # Ensure disconnecting the client

async def multithread_starter():
    if not os.path.exists("sessions"):
        os.mkdir("sessions")
    dirs = os.listdir("sessions/")
    sessions = list(filter(lambda x: x.endswith(".session"), dirs))
    sessions = list(map(lambda x: x.split(".session")[0], sessions))
    
    for session_name in sessions:
        logger = setup_logger(session_name)  # Create a logger for each session
        try:
            cli = NotPx("sessions/" + session_name)

            # Retry if the database is locked
            for attempt in range(5):
                try:
                    # Start painters and mine_claimers asynchronously
                    await asyncio.gather(
                        run_painters(cli, session_name, logger),
                        run_mine_claimer(cli, session_name, logger)
                    )
                    logger.info("Started both threads for session: {}".format(session_name))
                    break  # Exit loop on success
                except Exception as e:
                    if "database is locked" in str(e):
                        logger.error(f"Database locked. Retrying... Attempt {attempt + 1}/5")
                        time.sleep(1)  # Wait before retrying
                    else:
                        logger.error("Error on load session {}: {}".format(session_name, e))
                        print("[!] {}Error on load session{} \"{}\", error: {}".format(Colors.RED, Colors.END, session_name, e))
                        break  # Exit loop on non-lock errors

        except Exception as e:
            logger.error("Error on load session {}: {}".format(session_name, e))
            print("[!] {}Error on load session{} \"{}\", error: {}".format(Colors.RED, Colors.END, session_name, e))

async def add_account_session(api_id, api_hash):
    base_name = input("Enter base name for the session: ")
    unique_session_name = generate_unique_session_name(base_name)
    print(f"[+] Generated session name: {unique_session_name}")
    
    # Create a new Telegram client session
    client = TelegramClient(f"sessions/{unique_session_name}", api_id, api_hash)

    try:
        # Start the client and authorize
        await client.start()
        print(f"[+] Successfully created session: {unique_session_name}")
        # Save the session
        await client.disconnect()
    except Exception as e:
        print(f"[!] Failed to create session: {e}")

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
    clear_console()  # Clear console at the beginning
    print(r"""{}
  ███╗   ███╗  ██████╗  ██╗  ██╗ ███████╗ ██╗ ███╗   ██╗
  ████╗ ████║ ██╔═══██╗ ██║  ██║ ██╔════╝ ██║ ████╗  ██║
  ██╔████╔██║ ██║   ██║ ███████║ ███████╗ ██║ ██╔██╗ ██║
  ██║╚██╔╝██║ ██║   ██║ ██╔══██║ ╚════██║ ██║ ██║╚██╗██║
  ██║ ╚═╝ ██║ ╚██████╔╝ ██║  ██║ ███████║ ██║ ██║ ╚████║
  ╚═╝     ╚═╝  ╚═════╝  ╚═╝  ╚═╝ ╚══════╝ ╚═╝ ╚═╝  ╚═══╝ 
                                                
            NotPx Auto Paint & Claim by @Sakuingoo - v1.0 {}""".format(Colors.BLUE, Colors.END))

    start_bot_polling()  # Start polling at the beginning
    
    while True:
        print("\nMain Menu:")
        print("1. Add Account session")
        print("2. Start Mine + Claim")
        print("3. Reset API credentials")
        print("4. Reset session")
        print("5. Exit")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            api_id, api_hash = load_api_credentials()
            if api_id and api_hash:
                asyncio.run(add_account_session(api_id, api_hash))
            else:
                print("[!] API credentials not found. Please set them first.")

        elif choice == "2":
            api_id, api_hash = load_api_credentials()
            if api_id and api_hash:
                asyncio.run(multithread_starter())
            else:
                print("[!] API credentials not found. Please set them first.")

        elif choice == "3":
            reset_api_credentials()

        elif choice == "4":
            reset_session()

        elif choice == "5":
            stop_bot_polling()
            print("Exiting the program...")
            break

        else:
            print("[!] Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    process()
