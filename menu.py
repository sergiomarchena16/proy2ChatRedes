# First menu
def menu():
    print("WELCOME")
    print("OPTIONS")
    print("1. Register")
    print("2. Log in")
    op = input("Select and option: ")
    return op


# Principal
def menu_in():
    print("Activities: ")
    print("1. Show all users")
    print("2. Add user")
    print("3. Show contact details from user")
    print("4. Private chat")
    print("5. Send presence message")
    print("6. Chat with everyone")
    print("7. Send file")
    print("8. Exit session")
    print("9. Delete your account")
    op = input("Select one activity: ")
    return op


# Status
def show_menu():
    print("What do you wanna show? ")
    print("1. Chat")
    print("2. Away")
    print("3. Extended away")
    print("4. Do not disturb")
    op = input("==> ")
    return op