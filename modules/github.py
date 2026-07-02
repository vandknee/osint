from playwright.sync_api import sync_playwright

def check_github(username):
    url = f"https://github.com/{username}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        github_data={}

        page.goto(url)
        page.pause()

        if page.title() == "Page not found · GitHub · GitHub":
            github_data["result"]="NOT FOUND"
        else:
            name = page.locator(".p-name").inner_text()
            followers=page.locator("a[href$='?tab=followers'] span").inner_text()
            github_data["result"]="FOUND"
            github_data["name"]=name
            if page.locator(".p-note").is_visible():
                github_data["bio"]=page.locator(".p-note").inner_text()
            else:
                github_data["bio"]="None"
            github_data["followers"]=followers
            github_data["following"]=page.locator("a[href$='?tab=following'] span").inner_text()
            github_data["repositories"]=page.locator("a[href$='?tab=repositories'] span").first.inner_text()
            if page.locator(".p-org").is_visible():
                github_data["company"]=page.locator(".p-org").inner_text()
            else:
                github_data["company"]="None"
            
            if page.locator(".p-label").is_visible():
                github_data["location"]=page.locator(".p-label").inner_text()
            else:
                       github_data["location"]="None"
     
            page.screenshot(path=f"screenshots/{username}.png")    

        browser.close()

    return github_data 

