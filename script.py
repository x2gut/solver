from selenium import webdriver
from selenium.common import NoSuchElementException, InvalidSelectorException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import sqlite3
import time
import validators


class PortalTestSolver:
    def __init__(self, driver_path: str, headless: bool):
        self.question_to_answer = None
        self.options = webdriver.ChromeOptions()
        self.options.headless = headless
        self.driver = webdriver.Chrome(executable_path=driver_path, options=self.options)
        self.pages_count = 0

    def login(self, email: str, password: str):
        self.driver.get("https://op.tsatu.edu.ua/login/")
        user_enter_email = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "username")))
        user_enter_email.send_keys(email)
        user_enter_password = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "password")))
        user_enter_password.send_keys(password)
        self.driver.find_element(By.ID, "loginbtn").click()

        if "login" in self.driver.current_url:
            print("Неверный логин или пароль.")
            return False
        user_name = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "usertext"))).text
        print(f"Привет, {user_name.split(' ')[1]}")

        return True

    def find_correct_answers(self, test_url: str) -> dict:
        # Проверка ссылки на валид
        if not validators.url(test_url):
            print("Неправильная ссылка. Правильный формат -> https://.../...")
            return
        self.driver.get(test_url)
        time.sleep(1)
        # Проверка, количества оставшихся попыток
        try:
            if self.driver.find_element(By.XPATH, "//p[contains(text(), 'У Вас більше немає спроб')]") is not None:
                print("У вас больше нет попыток.")
                return

            if self.driver.find_element(By.XPATH, "//p[contains(text(), 'Кількість дозволених спроб: 1')]") is not None:
                print("В этом тесте разрешена только одна попытка. Я не могу пройти его.")
                return
            # Проверка есть ли вопросы
            if self.driver.find_element(By.CLASS_NAME, "alert-danger") is not None:
                print('В этом тесте нет вопросов!')
                return
        except NoSuchElementException:
            pass
        # Проверка, если неудачная попытка уже была совершенна, тогда мы не будем совершать её снова, а просто зайдем
        # на неё и возьмем ответы оттуда
        try:
            self.driver.find_element(By.XPATH, '//a[text()="Огляд"]').click()
            question_list = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "qtext")))
            right_answers_list = self.driver.find_elements(By.CLASS_NAME, "rightanswer")
        except NoSuchElementException:
            print('Ищу правильные ответы...')
            # Нажали на кнопку для прохождения теста
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-secondary"))).click()
            # Завершаем попытку, чтобы получить правильные ответы
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "endtestlink"))).click()
            # Подтверждаем завершение попытки
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[text()="Відправити все та завершити"]'))).click()
            # Окончательное подтверждение
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[4]/div[3]/div/div[2]/div/div[2]/input[1]"))).click()
            time.sleep(1)
            # Находим все правильные ответы
            question_list = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "qtext")))
            right_answers_list = self.driver.find_elements(By.CLASS_NAME, "rightanswer")
        questions = []
        answers = []

        for question in question_list:
            question_text = question.text
            questions.append(question_text)

        for right_answer in right_answers_list:
            right_answer_text = right_answer.text
            try:
                answer_split = right_answer_text.split('Правильні відповіді: ')[1]
                answers.append(answer_split)
            except IndexError:
                answer_split = right_answer_text.split("Правильна відповідь: ")[1]
                answers.append(answer_split)

        question_to_answer = {}

        for question, answer in zip(questions, answers):
            question_to_answer.setdefault(question, []).append(answer)
        return question_to_answer

    def get_results(self):
        mark = self.driver.find_element(By.XPATH, "//td[contains(text(), 'з можливих')]").text
        time = self.driver.find_element(By.XPATH, "//td[contains(text(), 'сек')]").text
        print(f"Оцінка: {mark}\n"
              f"Час: {time}\n"
              f"Если оценка меньше 10, возможно тест содержит изображения или спец. символы. В таком случае необходимо пройти его в ручную.")

    def solve_test(self, test_url: str, question_to_answer: dict):
        self.pages_count = 0
        self.driver.get(test_url)
        print("Прохожу тест...")
        # Нажимаем на кнопку для начала
        self.driver.find_element(By.CLASS_NAME, "btn-secondary").click()

        while "review" not in self.driver.current_url:
            question_list = []
            answer_list = []
            # Находим все тесты на страничке или теста, если он один
            questions_on_current_page = self.driver.find_elements(By.CLASS_NAME, "qtext")
            # Получаем текст каждого ответа и добавляем его в список
            answers_on_current_page = self.driver.find_elements(By.XPATH, "//label[@class='ml-1']")
            for answer_text in answers_on_current_page:
                answer_text = answer_text.text
                answer_list.append(answer_text[3:])
            # Получаем текст каждого вопроса и добавляем его в список
            for question_text in questions_on_current_page:
                question_text = question_text.text  # Получаем текст
                question_list.append(question_text)  # Добавляем в список
            for question in question_list:
                for answer in answer_list:
                    try:
                        try:
                            if self.driver.find_element(By.XPATH,
                                                        f"//div[contains(@class, 'qtext') and contains(text(), '{question}')]"):
                                for item in question_to_answer[question]:
                                    for question_item in question_to_answer.keys():
                                        if item == answer and question_item == question:
                                            try:
                                                self.driver.find_element(By.XPATH,
                                                                         f"//label[text()='{item}']").click()
                                                time.sleep(1)
                                            except InvalidSelectorException:
                                                self.driver.find_element(By.XPATH,
                                                                         f'//label[text()="{item}"]').click()
                                                time.sleep(1)
                        except InvalidSelectorException:
                            if self.driver.find_element(By.XPATH,
                                                        f'//div[contains(@class, "qtext") and contains(text(), "{question}")]'):
                                for item in question_to_answer[question]:
                                    for question_item in question_to_answer.keys():
                                        if item == answer and question_item == question:
                                            try:
                                                self.driver.find_element(By.XPATH,
                                                                         f'//label[text()="{item}"]').click()
                                                time.sleep(1)
                                            except InvalidSelectorException:
                                                print(InvalidSelectorException)
                                                self.driver.find_element(By.XPATH,
                                                                         f"//label[text()='{item}']").click()
                                                time.sleep(1)
                    except NoSuchElementException:
                        continue

            try:
                self.driver.find_element(By.NAME, "next").click()
                self.pages_count += 1
                print(f"Страница: {self.pages_count}")
                self.driver.find_element(By.XPATH,
                                         "/html/body/div[2]/div[3]/div/div/section[1]/div[1]/div[3]/div/div/form/button").click()
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[4]/div[3]/div/div[2]/div/div[2]/input[1]"))).click()
            except NoSuchElementException:
                continue

    def create_database(self, question_to_answer: dict):
        self.course_name = self.driver.find_element(By.XPATH, "/html/body/div[2]/div[3]/header/div/div/div/div[1]/div[1]/div/div/h1").text.replace(" ", "_")

        connection = sqlite3.connect("question_to_answer.db")
        cursor = connection.cursor()

        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {self.course_name}(
        question TEXT,
        answer TEXT)""")
        connection.commit()

        for question, answers in question_to_answer.items():
            for answer in answers:
                cursor.execute("SELECT * FROM {} WHERE question=? AND answer=?".format(self.course_name), (question, answer))
                result = cursor.fetchone()
                if result is None:
                    cursor.execute("INSERT INTO {}(question, answer) VALUES(?, ?)".format(self.course_name), (question, answer))

        connection.commit()

    def quit_driver(self):
        self.driver.quit()
