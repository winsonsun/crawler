import sys
import time
import httpx
import random
from typing import Dict, Any

def safe_probe(url: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    Performs a throttled, backoff-enabled HTTP request to probe a target.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    results = {
        "url": url,
        "status_code": None,
        "headers": {},
        "error": None,
        "is_cloudflare": False,
        "latency": 0
    }

    for attempt in range(max_retries):
        try:
            start_time = time.time()
            with httpx.Client(follow_redirects=True, timeout=10.0) as client:
                response = client.get(url, headers=headers)
            
            results["latency"] = time.time() - start_time
            results["status_code"] = response.status_code
            results["headers"] = dict(response.headers)
            
            server = response.headers.get("Server", "").lower()
            if "cloudflare" in server or "cf-ray" in response.headers:
                results["is_cloudflare"] = True
            
            if response.status_code == 200:
                break
            elif response.status_code == 429:
                wait_time = (2 ** attempt) + random.random()
                time.sleep(wait_time)
            else:
                break
                
        except Exception as e:
            results["error"] = str(e)
            wait_time = (2 ** attempt) + random.random()
            time.sleep(wait_time)

    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python safe_probe.py <url>")
        sys.exit(1)
        
    target_url = sys.argv[1]
    probe_results = safe_probe(target_url)
    
    # LLM-friendly output
    if probe_results["error"]:
        print(f"FAILURE: {probe_results['error']}")
    else:
        cf_status = "DETECTED" if probe_results["is_cloudflare"] else "Not detected"
        print(f"SUCCESS: {probe_results['url']} returned {probe_results['status_code']}")
        print(f"Cloudflare: {cf_status}")
        print(f"Latency: {probe_results['latency']:.2f}s")
        if probe_results["status_code"] != 200:
            print(f"Warning: Non-200 status. Check headers for rate limits or blocks.")
