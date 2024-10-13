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

class Colors:
    """Colors class for terminal output."""
    END = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"  # Added MAGENTA color

def get_bot_instance(bot_token):
    """Get or create a Telebot instance."""
    global valid_bot_token, token_expiration
    if bot_token not in bot_instances:
        bot_instances[bot_token] = telebot.TeleBot(bot_token)
    return bot_instances[bot_token]

async def run_mine_claimer(cli, session_name):
    """Run the mine claimer asynchronously."""
    await mine_claimer(cli, session_name)

async def run_painters(cli, session_name):
    """Run the painter asynchronously."""
    await painters(cli, session_name)

async def run_async_tasks(cli, session_name):
    """Run mine claimer and painter tasks together."""
    await asyncio.gather(
        run_mine_claimer(cli, session_name),
        run_painters(cli, session_name)
    )

def multithread_starter(bot_token):
    """Start multithreaded claiming and mining process."""
    print(f"{Colors.MAGENTA}✨ Starting the mining and claiming process... ✨{Colors.END}")

    if not os.path.exists("sessions"):
        os.mkdir("sessions")

    dirs = os.listdir("sessions/")
    sessions = [x.split(".session")[0] for x in dirs if x.endswith(".session")]

    if not sessions:
        print(f"{Colors.RED}[!] No sessions found.{Colors.END}")
        return

    for session_name in sessions:
        try:
            with lock:
                print(f"\n{Colors.CYAN}[+] Loading session: {session_name}{Colors.END}")
                cli = NotPx(f"sessions/{session_name}")

                print(f"{Colors.YELLOW}⚡ Running session for {session_name}.{Colors.END}")

                threading.Thread(target=asyncio.run, args=(run_async_tasks(cli, session_name),)).start()
        except Exception as e:
            print(f"{Colors.RED}[!] Error on loading session \"{session_name}\", error: {e}{Colors.END}")

def process():
    """Main process for starting the script and managing options."""
    global token_expiration, valid_bot_token

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

    bot = get_bot_instance(valid_bot_token)
    
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
