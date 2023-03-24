from script import PortalTestSolver
import art

solve_test = PortalTestSolver("chromedriver.exe",
                              headless=True)


def login_function():
    user_login = input("Введите вашу почту: ")
    user_password = input("Введите ваш пароль: ")
    # Проверка учётных данных
    if not solve_test.login(email=user_login, password=user_password):
        login_function()
    else:
        print("Успешный вход!")
        pass


def solve_function():
    while True:
        link_to_test = input('Ссылка на тест: ')
        # ...
        answers = solve_test.find_correct_answers(link_to_test)
        if not answers:
            solve_function()
        else:
            solve_test.solve_test(link_to_test, answers)
            solve_test.create_database(answers)
            solve_test.get_results()
            continue_or_exit = input("Continue? [y/n]: ")

            if continue_or_exit.lower() == "n":
                break


def main():
    print(art.text2art("TEST  SOLVER"))
    print("by x2gut:)")
    login_function()
    solve_function()


if __name__ == "__main__":
    main()
