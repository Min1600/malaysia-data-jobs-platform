from curl_cffi import requests
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/"
}
BASE_URL = f"https://my.jobstreet.com/data-analyst-jobs/in-Kuala-Lumpur"
params = {
    "keyword" : 'Data Analyst',
    "where" : 'Kuala Lumpur',
    "daterange": 1,
    "page": 1
}

PROXY_IP_1 = os.environ.get("PROXY_IP_1") 
PROXY_PORT_1 = os.environ.get("PROXY_PORT_1")  
PROXY_USER = os.environ.get("PROXY_USER") 
PROXY_PASS = os.environ.get("PROXY_PASS")  
print(PROXY_IP_1)
# Only build the dict if the secrets exist, preventing crashes
if all([PROXY_IP_1, PROXY_PORT_1, PROXY_USER, PROXY_PASS]):
    # Dynamically builds: http://user:pass@ip:port
    authenticated_proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_IP_1}:{PROXY_PORT_1}/"
    
    proxies = {
        "http": authenticated_proxy_url,
        "https": authenticated_proxy_url
    }
else:
    print("not found")
# test connection 
try:

    # requests data from jobstreet
    response = requests.get(BASE_URL, params=params, headers=HEADERS, proxies=proxies, impersonate="chrome120", timeout = 10)
    response.raise_for_status() # Automatically triggers HTTPError if status is 4xx or 5xx

except requests.exceptions.Timeout:
    print("⏱️ Request timed out after 10 seconds. Unable to determine number of pages. Aborting task!")


# Catches bad status codes (4xx or 5xx)
except requests.exceptions.HTTPError as e:
    status = e.response.status_code if e.response else "Unknown"
    reason = e.response.reason if e.response else str(e)

    print(f"🛑 HTTP Error: {status} - {reason}. Unable to determine number of pages. Aborting task!")


# Catches connection drops, timeouts, DNS issues where NO response was given
except requests.exceptions.RequestException as e:
    print(f"💥 Network level error occurred (No response received): {e}. Unable to determine number of pages aborting task!")
