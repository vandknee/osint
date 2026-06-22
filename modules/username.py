import requests
def check_github(username):
    url = f"https://github.com/{username}"

    response = requests.get(url)

    if response.status_code == 200:
        return "FOUND"
    else:
        return "NOT FOUND"
       