from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd

# Инициализация драйвера
driver = webdriver.Firefox()

# Открытие сайта
driver.get("https://kuper.ru/5ka")

# Функция для парсинга данных с одной страницы
def parse_page(soup, section_name):
    products = []
    for item in soup.find_all('div', class_='ProductCard_titleContainer__Kh_kg'):
        name = item.find('h3', class_='ProductCard_title__iB_Dr').text.strip()
        price_element = item.find_next('div', class_='ProductCardPrice_price__zSwp0')
        price = price_element.get_text(strip=True).replace('Цена за 1 шт.', '').strip() if price_element else "Не найдено"

        products.append({
            'name': name,
            'price': price,
            'category': section_name
        })
    return products

# Список для хранения всех продуктов
all_products = []

# Функция для навигации по разделам
def navigate_sections():
    try:
        # Получение всех разделов
        sections = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//nav/ul/li/a/div[2]/span'))
        )
        print(f"Найдено {len(sections)} разделов")

        for i in range(1, len(sections)):  # Начинаем со второго раздела
            # Перезагрузка элементов разделов после каждого клика
            sections = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//nav/ul/li/a/div[2]/span'))
            )
            if i >= len(sections):
                break
            section = sections[i]
            section_name = section.text
            print(f"Переход в раздел: {section_name}")
            section.click()
            time.sleep(5)  # Даем время на загрузку страницы

            # Нажатие на "Все товары категории"
            try:
                all_items_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//li[@class="NavigationTreeItem_root__WU7Qs"]/a'))
                )
                driver.execute_script("arguments[0].scrollIntoView();", all_items_link)
                driver.execute_script("arguments[0].click();", all_items_link)
                time.sleep(5)  # Даем время на загрузку страницы
            except Exception as e:
                print(f"Не удалось найти ссылку 'Все товары категории' в разделе {section_name}: {e}")
                continue

            # Парсинг данных со страницы
            while True:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                products = parse_page(soup, section_name)
                for product in products:
                    if product not in all_products:
                        all_products.append(product)
                print(f"Собрано {len(products)} продуктов в разделе {section_name}")

                try:
                    # Нажатие на кнопку "Показать еще"
                    show_more_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Показать еще")]'))
                    )
                    driver.execute_script("arguments[0].scrollIntoView();", show_more_button)
                    driver.execute_script("arguments[0].click();", show_more_button)
                    time.sleep(3)  # Даем время на загрузку новых товаров
                except Exception as e:
                    print(f"Не удалось найти кнопку 'Показать еще' в разделе {section_name}: {e}")
                    break

            # Возвращение на главную страницу
            try:
                back_to_home_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//a[@class="NavigationLink_root__qkntj NavigationTreeContainer_toHomeLink___YOuw"]'))
                )
                driver.execute_script("arguments[0].scrollIntoView();", back_to_home_link)
                driver.execute_script("arguments[0].click();", back_to_home_link)
                time.sleep(5)  # Даем время на загрузку главной страницы
            except Exception as e:
                print(f"Не удалось вернуться на главную страницу из раздела {section_name}: {e}")
                break

            # Проверка, является ли текущий раздел "Приготовить дома"
            if section_name == "Овощи, фрукты, зелень, орехи": ## должно быть "Приготовить дома"
                break
    except Exception as e:
        print(f"Ошибка при навигации по разделам: {e}")

# Навигация по разделам и парсинг данных
navigate_sections()

# Закрытие драйвера
driver.close()

# Сохранение данных в DataFrame
df = pd.DataFrame(all_products)
df.to_csv('products.csv', index=False)

print("Данные успешно собраны и сохранены в products.csv")
