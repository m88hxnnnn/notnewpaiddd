import time
import random
import asyncio
from bot.utils import night_sleep, Colors

async def mine_claimer(NotPxClient, session_name):
    await asyncio.sleep(5)  # Start with a delay...
    print("[+] {}Auto claiming started{}.".format(Colors.CYAN, Colors.END))
    while True:
        await night_sleep()  # Check and sleep if it's between 12-1 AM Iran time
        acc_data = NotPxClient.accountStatus()

        if acc_data is None:
            print("[!] {}{}{}: {}Failed to retrieve account status. Retrying...{}".format(Colors.CYAN, session_name, Colors.END, Colors.RED, Colors.END))
            await asyncio.sleep(5)
            continue

        if 'fromStart' in acc_data and 'speedPerSecond' in acc_data:
            fromStart = acc_data['fromStart']
            speedPerSecond = acc_data['speedPerSecond']
            maxMiningTime = acc_data['maxMiningTime'] / 60
            random_recharge_speed = random.randint(30, 90)

            claimed_count = 0
            while claimed_count < 10:
                current_claim = NotPxClient.claim_mining()
                claimed_count += current_claim
                print(f"[+] Claimed {current_claim} points. Total: {claimed_count} points.")

                if claimed_count >= 10:
                    print(f"[+] {session_name}: Successfully claimed 10 points.")
                    break

            print("[!] {}{}{}: Sleeping for {} minutes...".format(Colors.CYAN, session_name, Colors.END, round((maxMiningTime + random_recharge_speed) / 60), 2))
            await asyncio.sleep(maxMiningTime + random_recharge_speed)
        else:
            print("[!] {}{}{}: {}Unexpected account data format. Retrying...{}".format(Colors.CYAN, session_name, Colors.END, Colors.RED, Colors.END))
