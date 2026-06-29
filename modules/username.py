from playwright.sync_api import sync_playwright

def check_github(username):
    url = f"https://github.com/{username}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)

        if page.title() == "Page not found · GitHub · GitHub":
            result = "NOT FOUND"
        else:
            result = "FOUND"

        browser.close()

    return result