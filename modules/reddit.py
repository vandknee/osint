from playwright.sync_api import sync_playwright

def check_reddit(username):
    url = f"https://www.reddit.com/user/{username}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Opens a browser
        page = browser.new_page()

        page.goto(url)

        title = page.title()

        print("Page title:", title)

        browser.close()