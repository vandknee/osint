from playwright.sync_api import sync_playwright

def check_github(username):
    url = f"https://github.com/{username}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(url)
        page.pause()
        name = page.locater(".p-name").inner_text()
        print(name)

        if page.title() == "Page not found · GitHub · GitHub":
            result = "NOT FOUND"
        else:
            result = "FOUND"
        page.screenshot(path=f"screenshots/{username}.png")    

        browser.close()

    return result