import requests
import random
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

class ProxyManager:
    def __init__(self, proxy_sources):
        self.proxy_sources = proxy_sources
        self.working_proxies = []
        self.test_url = "https://groups.roblox.com/v1/groups/1"

    def fetch_proxies(self):
        """Fetch proxies from multiple sources"""
        proxies = []
        for source in self.proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                proxies.extend([p.strip() for p in response.text.split('\n') if p.strip()])
            except:
                continue
        return list(set(proxies))

    def test_proxy(self, proxy):
        """Test both HTTP and SOCKS proxies with increased timeout"""
        try:
            # Test HTTP
            response = requests.get(
                self.test_url,
                proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                timeout=10
            )
            if response.status_code == 200:
                return proxy
            
            # Test SOCKS
            response = requests.get(
                self.test_url,
                proxies={"http": f"socks5://{proxy}", "https": f"socks5://{proxy}"},
                timeout=10
            )
            return proxy if response.status_code == 200 else None
        except:
            return None

    def validate_proxies(self, max_workers=100):
        """Validate proxies with progress tracking"""
        proxies = self.fetch_proxies()
        total = len(proxies)
        self.working_proxies = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.test_proxy, proxy): proxy for proxy in proxies}
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                proxy = futures[future]
                result = future.result()
                if result:
                    self.working_proxies.append(result)
                print(f"Progress: {i+1}/{total} proxies tested", end="\r")
        
        print(f"\nFound {len(self.working_proxies)} working proxies")
        return self.working_proxies

    def get_random_proxy(self):
        """Get a random working proxy"""
        return random.choice(self.working_proxies) if self.working_proxies else None