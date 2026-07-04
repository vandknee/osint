from modules.github import check_github

username = input("Enter username: ").strip()
check_github(username)