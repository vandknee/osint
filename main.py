from modules.username import check_github

username = input("Enter username: ")

result = check_github(username)

print(f"GitHub account: {result}")