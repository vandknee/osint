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
                github_data["bio"] = None
            github_data["followers"]=followers
            github_data["following"]=page.locator("a[href$='?tab=following'] span").inner_text()
            github_data["repositories"]=page.locator("a[href$='?tab=repositories'] span").first.inner_text()
            
            if page.locator(".p-org").is_visible():
                github_data["company"]=page.locator(".p-org").inner_text()
            else:
                github_data["company"] = None
            
            if page.locator(".p-label").is_visible():
                github_data["location"]=page.locator(".p-label").inner_text()
            else:
                       github_data["location"] = None

            
            github_data["websites"] = []
            websites = page.locator('a[rel~="nofollow"]')
            for i in range(websites.count()):
                github_data["websites"].append(
                    websites.nth(i).get_attribute("href")
            )

            github_data["profile_url"] = url    
     
            page.screenshot(path=f"screenshots/{username}.png")

            if page.locator("d-inline-block mb-2").is_visible():
                 github_data["Date Joined"] = page.locator("d-inline-block mb-2").inner_text()
            else:
                 github_data["Date Joined"] = None
                
            github_data["pinned_repos"] = []
            pinned_heading = page.locator("h2", has_text="Pinned")
            if pinned_heading.count() > 0:
                # Find every repository name in the pinned section
                repos = page.locator("span.repo")
                for i in range(repos.count()):
                    repo_name = repos.nth(i).inner_text()
                    github_data["pinned_repos"].append(repo_name)
            else:
                github_data["pinned_repos"] = []


            # Popular Repositories
            github_data["popular_repos"] = []
            # Look for an <h2> whose text is "Popular repositories"
            popular_heading = page.locator("h2", has_text="Popular repositories")
            if popular_heading.count() > 0:
                repos = page.locator("span.repo")
                for i in range(repos.count()):
                    repo_name = repos.nth(i).inner_text()
                    github_data["popular_repos"].append(repo_name)
            else:
                github_data["popular_repos"] = []
        browser.close()

    return github_data
