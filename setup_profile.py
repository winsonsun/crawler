# setup_profile.py
import asyncio
import argparse
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def setup(profile_dir: str, site_url: str, remote_debugging_port: int):
    """
    Launches a browser with a persistent profile to allow the user to manually
    solve a Cloudflare challenge, saving the resulting clearance cookie.
    """
    print(f"Launching browser with profile directory: '{profile_dir}'")
    if remote_debugging_port:
        print(f"  -- Remote debugging enabled on port {remote_debugging_port}")
    print("Please navigate to the target site, solve any 'human verification' challenges,")
    print("and then close the browser window to save the session.")

    extra_args = []
    if remote_debugging_port:
        extra_args.append(f"--remote-debugging-port={remote_debugging_port}")

    browser_config = BrowserConfig(
        headless=False,
        user_data_dir=profile_dir,
        use_managed_browser=True,
        extra_args=extra_args
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # This will open a browser window.
        # The user manually navigates and solves the captcha.
        # Once they see the real homepage, they can close the browser.
        await crawler.arun(url=site_url)
    
    print(f"\nProfile setup complete. The session cookie has been saved in '{profile_dir}'.")
    print("You can now run the main crawler with the --user-data-dir argument pointing to this directory.")

def main():
    parser = argparse.ArgumentParser(
        description="""
        One-time setup script to create a browser profile and solve a Cloudflare
        challenge manually. The resulting session cookie will be saved and can be
        reused by the main crawler.
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--profile-dir",
        default="./chrome-profile",
        help="The directory to create and store the browser profile in (default: ./chrome-profile)"
    )
    parser.add_argument(
        "--site-url",
        default="https://javdb.com",
        help="The URL of the target site to visit for solving the challenge (default: https://javdb.com)"
    )
    parser.add_argument(
        "--remote-debugging-port",
        type=int,
        default=0,
        help="""
Enable remote debugging. To use:
  1. Start this script on your server with a port (e.g., --remote-debugging-port=9222).
  2. On your local machine, create an SSH tunnel:
     ssh -L 9222:localhost:9222 your_user@your_server_ip
  3. On your local machine, open Chrome and go to: chrome://inspect
  4. Click 'Configure...' and add 'localhost:9222' to the list.
  5. The remote browser should appear as a target. Click 'inspect' to control it.
"""
    )
    args = parser.parse_args()
    
    asyncio.run(setup(args.profile_dir, args.site_url, args.remote_debugging_port))

if __name__ == "__main__":
    main()
