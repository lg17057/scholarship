user_age = float(input("Enter your age: "))

if user_age < 18:
    print("You may not drive or drink.")
elif user_age >= 18 and user_age < 21:
    print("You may drive but not drink.")
elif user_age >= 21:
    print("You may drive and drink, but never drive after drinking!")
