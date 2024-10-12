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
import telebot
from datetime import datetime, timedelta

# Global variables
bot_instances = {}
lock = threading.Lock()
token_expiration = None  # To store the token expiration time
valid_bot_token = None  # To store the valid bot token

# Colors class with additional colors
class Colors:
    END = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"  # Added MAGENTA color

def get_bot_instance(bot_token):
    global valid_bot_token, token_expiration
    if bot_token not in bot_instances:
        bot_instances[bot_token] = telebot.TeleBot(bot_token)
    return bot_instances[bot_token]

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

def multithread_starter(bot_token):
    print(f"{Colors.MAGENTA}✨ Starting the mining and claiming process... ✨{Colors.END}")

    if not os.path.exists("sessions"):
        os.mkdir("sessions")

    dirs = os.listdir("sessions/")
    sessions = list(filter(lambda x: x.endswith(".session"), dirs))
    sessions = list(map(lambda x: x.split(".session")[0], sessions))

    if not sessions:
        print(f"{Colors.RED}[!] No sessions found.{Colors.END}")
        return

    for session_name in sessions:
        try:
            with lock:
                print(f"\n{Colors.CYAN}[+] Loading session: {session_name}{Colors.END}")
                cli = NotPx("sessions/" + session_name)

                print(f"{Colors.YELLOW}⚡ Running without proxy for {session_name}.{Colors.END}")

                threading.Thread(target=run_async_functions, args=(cli, session_name)).start()
        except Exception as e:
            print(f"{Colors.RED}[!] Error on loading session \"{session_name}\", error: {e}{Colors.END}")

def add_api_credentials():
    api_id = input(f"{Colors.BLUE}🔑 Enter API ID: {Colors.END}")
    api_hash = input(f"{Colors.BLUE}🔑 Enter API Hash: {Colors.END}")
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env.txt')
    with open(env_path, "w") as f:
        f.write(f"API_ID={api_id}\n")
        f.write(f"API_HASH={api_hash}\n")
    print(f"{Colors.GREEN}[+] API credentials saved successfully in env.txt file.{Colors.END}")

def reset_api_credentials():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'env.txt')
    if os.path.exists(env_path):
        os.remove(env_path)
        print(f"{Colors.GREEN}[+] API credentials reset successfully.{Colors.END}")
    else:
        print(f"{Colors.RED}[!] No env.txt file found. Nothing to reset.{Colors.END}")

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
    print(f"\n{Colors.GREEN}[+] Active Sessions:{Colors.END}")
    sessions = load_sessions()
    if sessions:
        for session in sessions:
            print(f" - {Colors.CYAN}{session}{Colors.END}")
    else:
        print(f"{Colors.RED}[!] No active sessions found.{Colors.END}")

def process():
    global token_expiration, valid_bot_token

    # Clearing screen before running
    os.system('cls' if os.name == 'nt' else 'clear')

    print(r"""  
        ███╗   ███╗  ██████╗  ██╗  ██╗ ███████╗ ██╗ ███╗   ██╗
        ████╗ ████║ ██╔═══██╗ ██║  ██║ ██╔════╝ ██║ ████╗  ██║
        ██╔████╔██║ ██║   ██║ ███████║ ███████╗ ██║ ██╔██╗ ██║
        ██║╚██╔╝██║ ██║   ██║ ██╔══██║ ╚════██║ ██║ ██║╚██╗██║
        ██║ ╚═╝ ██║ ╚██████╔╝ ██║  ██║ ███████║ ██║ ██║ ╚████║
        ╚═╝     ╚═╝  ╚═════╝  ╚═╝  ╚═╝ ╚══════╝ ╚═╝ ╚═╝  ╚═══╝
                                                
        🌟 NotPx Auto Paint & Claim by @helpppeeerrrrrr - v1.0 🌟""")

    if valid_bot_token is None or datetime.now() >= token_expiration:
        bot_token = input(f"{Colors.BLUE}🔑 Enter your bot token: {Colors.END}")
        valid_bot_token = bot_token
        token_expiration = datetime.now() + timedelta(hours=2)
        print(f"{Colors.GREEN}[+] Your bot token is valid for 2 hours from now.{Colors.END}")
    else:
        print(f"{Colors.GREEN}[+] Using cached bot token. It is valid until {token_expiration}.{Colors.END}")

    bot = get_bot_instance(valid_bot_token)  # Get the bot instance with the valid token
    
    bot_thread = threading.Thread(target=bot.polling, kwargs={"none_stop": True})
    bot_thread.start()
    
    while True:
        print("\n{0}✨ Main Menu: ✨{1}".format(Colors.YELLOW, Colors.END))
        print("1. Add Account Session")
        print("2. Start Mine + Claim")
        print("3. Show Active Sessions")
        print("4. Add API ID and Hash")
        print("5. Reset API Credentials")
        print("6. Reset Session")
        print("7. Exit")
        
        option = input(f"{Colors.BLUE}🔍 Enter your choice: {Colors.END}")
        
        if option == "1":
            name = input(f"\n{Colors.CYAN}📁 Enter Session name: {Colors.END}")
            if not os.path.exists(f"sessions/{name}.session"):
                print(f"{Colors.RED}[!] Session \"{name}\" does not exist.{Colors.END}")
            else:
                save_session(name)
                print(f"{Colors.GREEN}[+] Session \"{name}\" added successfully.{Colors.END}")
                
        elif option == "2":
            multithread_starter(valid_bot_token)
            print(f"{Colors.YELLOW}✨ Back to Main Menu... ✨{Colors.END}")  # Indicates returning to menu after claiming
            
        elif option == "3":
            show_sessions()
        
        elif option == "4":
            add_api_credentials()
        
        elif option == "5":
            reset_api_credentials()
        
        elif option == "6":
            session_name = input(f"{Colors.CYAN}📄 Enter the session name to reset: {Colors.END}")
            if os.path.exists(f"sessions/{session_name}.session"):
                os.remove(f"sessions/{session_name}.session")
                print(f"{Colors.GREEN}[+] Session \"{session_name}\" reset successfully.{Colors.END}")
            else:
                print(f"{Colors.RED}[!] Session \"{session_name}\" not found.{Colors.END}")
        
        elif option == "7":
            print(f"{Colors.YELLOW}🌟 Exiting... 🌟{Colors.END}")
            bot.stop_polling()
            bot_thread.join()
            break

        else:
            print(f"{Colors.RED}[!] Invalid option. Please try again.{Colors.END}")

if __name__ == "__main__":
    if not os.path.exists("sessions"):
        os.mkdir("sessions")
    load_sessions()  # Load existing sessions
    process()  # Start the process
