import time
import os
import requests
import concurrent.futures
from proxy_manager import ProxyManager
from config import PROXY_SOURCES
from cookie_free_scanner import CookieFreeScanner

DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1382617372615118888/bX7d1fUjSUh-mrRIFlo07J_hWMy5A26sPPd_PHpyCYbpP9ieDnraBsTPAram9JF1ttNd"

START_ID = 1000000
END_ID = 17412877
BATCH_SIZE = 10000  # Number of groups to scan per cycle

def send_to_discord(group_id):
    data = {
        "content": f"Unclaimed group found: https://www.roblox.com/groups/{group_id}"
    }
    requests.post(DISCORD_WEBHOOK_URL, json=data)

def claim_group(group_id, roblosecurity_cookie):
    url = f"https://groups.roblox.com/v1/groups/{group_id}/claim-ownership"
    headers = {
        "Cookie": f".ROBLOSECURITY={roblosecurity_cookie}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print(f"✅ Claimed group {group_id}")
    else:
        print(f"❌ Failed to claim group {group_id}: {response.text}")

def load_last_id():
    if os.path.exists("progress.txt"):
        with open("progress.txt", "r") as f:
            return int(f.read().strip())
    return START_ID

def save_last_id(last_id):
    with open("progress.txt", "w") as f:
        f.write(str(last_id))

def run_once(roblosecurity_cookie):
    last_id = load_last_id()
    next_id = min(last_id + BATCH_SIZE, END_ID)
    print(f"🔍 Scanning group IDs from {last_id} to {next_id}...")

    proxy_manager = ProxyManager(PROXY_SOURCES)
    working_proxies = proxy_manager.validate_proxies(max_workers=500)
    if not working_proxies:
        print("No working proxies found. Exiting cycle.")
        return

    scanner = CookieFreeScanner(working_proxies)
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(scanner.check_group, group_id): group_id for group_id in range(last_id, next_id)}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            if result and result['unclaimed'] and result['open']:
                results.append(result['group_id'])
                send_to_discord(result['group_id'])
                claim_group(result['group_id'], roblosecurity_cookie)
            if (i + 1) % 100 == 0:
                print(f"Progress: {i+1}/{next_id - last_id} checked | Found: {len(results)}", flush=True)

    with open('unclaimed_groups.txt', 'a') as f:
        for group_id in results:
            f.write(f"{group_id}\n")

    save_last_id(next_id)
    print(f"✅ Finished scanning up to ID {next_id}. Sleeping for 10 minutes...\n")

if __name__ == "__main__":
    def load_cookie():
        if not os.path.exists("cookie.txt"):
            print("❌ 'cookie.txt' not found. Please create it with your ROBLOSECURITY cookie.")
            exit()
        with open("cookie.txt", "r") as f:
            return f.read().strip()

    roblosecurity_cookie = load_cookie()

    while True:
        run_once(roblosecurity_cookie)
        if load_last_id() >= END_ID:
            print("🎉 All groups scanned! Exiting.")
            break
        time.sleep(600)  # Wait 10 minutes
