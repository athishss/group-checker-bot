import time
import os
import requests
import concurrent.futures
from proxy_manager import ProxyManager
from config import PROXY_SOURCES
from cookie_free_scanner import CookieFreeScanner

# Discord webhook
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1382617372615118888/bX7d1fUjSUh-mrRIFlo07J_hWMy5A26sPPd_PHpyCYbpP9ieDnraBsTPAram9JF1ttNd"

# Group ID range
START_ID = 1000000
END_ID = 17412877
BATCH_SIZE = 10000  # Number of groups to scan per batch

def send_to_discord(group_id):
    """Send a message to Discord when a group is found"""
    data = {
        "content": f"Unclaimed group found: https://www.roblox.com/groups/{group_id}"
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠️ Failed to send to Discord for group {group_id}: {e}")

def claim_group(group_id, roblosecurity_cookie):
    """Claim ownership of a group with retries"""
    url = f"https://groups.roblox.com/v1/groups/{group_id}/claim-ownership"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f".ROBLOSECURITY={roblosecurity_cookie}",
        "Content-Type": "application/json"
    }

    for attempt in range(3):  # Try 3 times max
        try:
            response = requests.post(url, headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"✅ Claimed group {group_id}")
                return
            else:
                print(f"❌ Attempt {attempt + 1}: Failed to claim {group_id} - {response.status_code} - {response.text}")
        except requests.RequestException as e:
            print(f"⚠️ Attempt {attempt + 1}: Request error while claiming group {group_id}: {e}")
        time.sleep(1)  # brief wait before retry

def load_last_id():
    """Load the last scanned group ID from progress.txt"""
    if os.path.exists("progress.txt"):
        with open("progress.txt", "r") as f:
            return int(f.read().strip())
    return START_ID

def save_last_id(last_id):
    """Save the last scanned group ID to progress.txt (with backup)"""
    with open("progress_backup.txt", "w") as backup:
        backup.write(str(last_id))
    with open("progress.txt", "w") as f:
        f.write(str(last_id))

def load_cookie():
    """Load the .ROBLOSECURITY cookie from cookie.txt"""
    if not os.path.exists("cookie.txt"):
        print("❌ 'cookie.txt' not found. Please create it with your ROBLOSECURITY cookie.")
        exit()
    with open("cookie.txt", "r") as f:
        return f.read().strip()

def run_once(roblosecurity_cookie):
    """Scan one batch of groups"""
    last_id = load_last_id()
    next_id = min(last_id + BATCH_SIZE, END_ID)
    print(f"🔍 Scanning group IDs from {last_id} to {next_id}...")

    proxy_manager = ProxyManager(PROXY_SOURCES)
    working_proxies = proxy_manager.validate_proxies(max_workers=500)
    if not working_proxies:
        print("❌ No working proxies found. Exiting cycle.")
        return

    scanner = CookieFreeScanner(working_proxies)
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=1500) as executor:
        futures = {executor.submit(scanner.check_group, group_id): group_id for group_id in range(last_id, next_id)}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            try:
                result = future.result()
                if result and result['unclaimed'] and result['open']:
                    results.append(result['group_id'])
                    send_to_discord(result['group_id'])
                    claim_group(result['group_id'], roblosecurity_cookie)
            except Exception as e:
                print(f"⚠️ Error checking group: {e}")
            if (i + 1) % 10 == 0:
                print(f"Progress: {i+1}/{next_id - last_id} checked | Found: {len(results)}", flush=True)

    with open('unclaimed_groups.txt', 'a') as f:
        for group_id in results:
            f.write(f"{group_id}\n")

    save_last_id(next_id)
    print(f"✅ Finished scanning up to ID {next_id}.\n")

if __name__ == "__main__":
    roblosecurity_cookie = load_cookie()

    while True:
        run_once(roblosecurity_cookie)
        if load_last_id() >= END_ID:
            print("🎉 All groups scanned! Exiting.")
            break
        print("⏳ Sleeping for 10 minutes before next batch...\n")
        time.sleep(60)  # 10-minute delay
