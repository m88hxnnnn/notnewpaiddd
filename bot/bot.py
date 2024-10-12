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

# Colors class for retro-style text
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'  # To reset the color

# Global variables
bot_instances = {}
lock = threading.Lock()
token_expiration = None  # To store the token expiration time
valid_bot_token = None  # To store the valid bot token
proxies = {}  # To store proxies

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
    print(f"{Colors.YELLOW}Starting the mining and claiming process...{Colors.END}")

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
                print(f"{Colors.GREEN}[+] Loading session: {session_name}{Colors.END}")
                cli = NotPx("sessions/" + session_name)

                proxy = proxies.get(session_name)
                if proxy:
                    print(f"{Colors.GREEN}[+] Using proxy: {proxy} for {session_name}{Colors.END}")
                else:
                    print(f"{Colors.YELLOW}[!] No proxy found for session {session_name}, running without proxy.{Colors.END}")

                threading.Thread(target=run_async_functions, args=(cli, session_name, proxy)).start()
        except Exception as e:
            print(f"{Colors.RED}[!] Error on load session \"{session_name}\", error: {e}{Colors.END}")

def create_proxy_folder():
    if not os.path.exists("proxies"):
        os.makedirs("proxies")
        print(f"{Colors.GREEN}[+] Proxy folder created.{Colors.END}")

def add_proxy():
    session_name = input(f"{Colors.CYAN}Enter the session name for proxy: {Colors.END}")
    proxy = input(f"{Colors.CYAN}Enter proxy (format: http://username:password@ip:port): {Colors.END}")

    # Validate the proxy format
    if not proxy.startswith("http://") or not proxy.count(":") == 3:
        print(f"{Colors.RED}[!] Invalid proxy format. Please use http://username:password@ip:port format.{Colors.END}")
        return

    # Save the proxy to a file
    with open(f"proxies/{session_name}_proxy.txt", "w") as f:
        f.write(proxy)
    
    print(f"{Colors.GREEN}[+] Proxy {proxy} added for {session_name}.{Colors.END}")

def load_proxies():
    proxies.clear()  # Clear existing proxies to avoid duplicates
    create_proxy_folder()  # Ensure the proxy folder exists
    if os.path.exists("proxies"):
        for filename in os.listdir("proxies"):
            if filename.endswith("_proxy.txt"):
                session_name = filename.split("_proxy.txt")[0]
                with open(f"proxies/{filename}", "r") as f:
                    proxy = f.read().strip()
                    proxies[session_name] = proxy
                    print(f"{Colors.GREEN}[+] Loaded proxy {proxy} for {session_name}.{Colors.END}")
    else:
        print(f"{Colors.YELLOW}[!] No proxy files found.{Colors.END}")

def reset_proxy():
    session_name = input(f"{Colors.CYAN}Enter the session name to reset proxy: {Colors.END}")
    proxy_file = f"proxies/{session_name}_proxy.txt"
    if os.path.exists(proxy_file):
        os.remove(proxy_file)
        print(f"{Colors.GREEN}[+] Proxy reset for {session_name}.{Colors.END}")
    else:
        print(f"{Colors.RED}[!] No proxy found for {session_name}.{Colors.END}")

def add_api_credentials():
    api_id = input(f"{Colors.CYAN}Enter API ID: {Colors.END}")
    api_hash = input(f"{Colors.CYAN}Enter API Hash: {Colors.END}")
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
    print(f"{Colors.BOLD}{Colors.CYAN}[+] Active Sessions:{Colors.END}")
    sessions = load_sessions()
    if sessions:
        for session in sessions:
            print(f"{Colors.GREEN} - {session}{Colors.END}")
    else:
        print(f"{Colors.RED}[!] No active sessions found.{Colors.END}")

def process():
    global token_expiration, valid_bot_token

    # Clear terminal screen before starting
    os.system('cls' if os.name == 'nt' else 'clear')

    # Load proxies on startup
    load_proxies()

    print(r"""  
        {red}███╗   ███╗  ██████╗  ██╗  ██╗ ███████╗ ██╗ ███╗   ██╗
        ████╗ ████║ ██╔═══██╗ ██║  ██║ ██╔════╝ ██║ ████╗  ██║
        ██╔████╔██║ ██║   ██║ ███████║ ███████╗ ██║ ██╔██╗ ██║
        ██║╚██╔╝██║ ██║   ██║ ██╔══██║ ╚════██║ ██║ ██║╚██╗██║
        ██║ ╚═╝ ██║ ╚██████╔╝ ██║  ██║ ███████║ ██║ ██║ ╚████║
        ╚═╝     ╚═╝  ╚═════╝  ╚═╝  ╚═╝ ╚══════╝ ╚═╝ ╚═╝  ╚═══╝{end}
                                                
        {blue}NotPx Auto Paint & Claim by @helpppeeerrrrrr - v1.0{end}
    """.format(red=Colors.RED, blue=Colors.BLUE, end=Colors.END))
    
    if valid_bot_token is None or datetime.now() >= token_expiration:
        bot_token = input(f"{Colors.CYAN}Enter your bot token: {Colors.END}")
        valid_bot_token = bot_token
        token_expiration = datetime.now() + timedelta(hours=2)
        print(f"{Colors.GREEN}[+] Your bot token is valid for 2 hours from now.{Colors.END}")
    else:
        print(f"{Colors.GREEN}[+] Using cached bot token. It is valid until {token_expiration}.{Colors.END}")
    
    bot = get_bot_instance(valid_bot_token)  # Get the bot instance with the valid token
    
    bot_thread = threading.Thread(target=bot.polling, kwargs={"none_stop": True})
    bot_thread.start()
    
    while True:
        print(f"\n{Colors.BOLD}{Colors.CYAN}Main Menu:{Colors.END}")
        print(f"{Colors.GREEN}1.{Colors.END} Add Account session")
        print(f"{Colors.GREEN}2.{Colors.END} Start Mine + Claim")
        print(f"{Colors.GREEN}3.{Colors.END} Show Active Sessions")
        print(f"{Colors.GREEN}4.{Colors.END} Add API ID and Hash")
        print(f"{Colors.GREEN}5.{Colors.END} Reset API Credentials")
        print(f"{Colors.GREEN}6.{Colors.END} Reset Session")
        print(f"{Colors.GREEN}7.{Colors.END} Add Proxy")
        print(f"{Colors.GREEN}8.{Colors.END} Reset Proxy")
        print(f"{Colors.GREEN}9.{Colors.END} Exit")
        
        option = input(f"{Colors.CYAN}Enter your choice: {Colors.END}")
        
        if option == "1":
            name = input(f"\n{Colors.CYAN}Enter Session name: {Colors.END}")
            if not os.path.exists(f"sessions/{name}.session"):
                print(f"{Colors.RED}[!] Session \"{name}\" does not exist.{Colors.END}")
            else:
                save_session(name)
                print(f"{Colors.GREEN}[+] Session \"{name}\" added successfully.{Colors.END}")
                
        elif option == "2":
            multithread_starter(valid_bot_token)
            
        elif option == "3":
            show_sessions()
        
        elif option == "4":
            add_api_credentials()
        
        elif option == "5":
            reset_api_credentials()
        
        elif option == "6":
            session_name = input(f"{Colors.CYAN}Enter the session name to reset: {Colors.END}")
            if os.path.exists(f"sessions/{session_name}.session"):
                os.remove(f"sessions/{session_name}.session")
                print(f"{Colors.GREEN}[+] Session \"{session_name}\" reset successfully.{Colors.END}")
            else:
                print(f"{Colors.RED}[!] Session \"{session_name}\" not found.{Colors.END}")
        
        elif option == "7":
            add_proxy()
        
        elif option == "8":
            reset_proxy()

        elif option == "9":
            print(f"{Colors.MAGENTA}[+] Exiting...{Colors.END}")
            break
        
        else:
            print(f"{Colors.RED}[!] Invalid option. Please try again.{Colors.END}")

if __name__ == "__main__":
    process()
