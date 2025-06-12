import requests
import random

class CookieFreeScanner:
    def __init__(self, working_proxies):
        """Initialize the scanner with a list of working proxies"""
        self.working_proxies = working_proxies

    def check_group(self, group_id):
        """Check if a group is unclaimed and open"""
        proxy = random.choice(self.working_proxies)
        try:
            response = requests.get(
                f"https://groups.roblox.com/v1/groups/{group_id}",
                proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'group_id': group_id,
                    'unclaimed': data.get('owner') is None,
                    'open': data.get('publicEntryAllowed', False) and not data.get('isLocked', True)
                }
            elif response.status_code == 429:
                # Remove rate-limited proxy
                self.working_proxies.remove(proxy)
        except:
            pass
        return None