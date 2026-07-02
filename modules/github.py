from playwright.sync_api import sync_playwright

def check_github(username):
    url = f"https://github.com/{username}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        github_data={}

        page.goto(url)
        page.pause()

        if page.title() == "Page not found · GitHub · GitHub":
            github_data["result"]="NOT FOUND"
        else:
            name = page.locator(".p-name").inner_text()
            bio = page.locator(".p-note").inner_text()
            github_data["result"]="FOUND"
            github_data["name"]=name
            github_data["bio"]=bio
            page.screenshot(path=f"screenshots/{username}.png")    

        browser.close()

    return github_data 