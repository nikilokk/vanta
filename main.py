from brain import ask_ai


print("Vanta online.")


while True:

    user_input = input("\nТы: ")

    if user_input.lower() in {
        "exit",
        "quit",
        "выход",
    }:
        break

    response = ask_ai(user_input)

    print("\nVanta:", response)