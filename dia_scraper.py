import os
import re
import sys
import time
import subprocess
import json

try:
    import requests
    import chromedriver_autoinstaller
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium import webdriver
    # import undetected_chromedriver
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    subprocess.check_call([sys.executable, "-m", "pip",
                          "install", "undetected_chromedriver"])
    subprocess.check_call([sys.executable, "-m", "pip",
                          "install", "chromedriver_autoinstaller"])
    import requests
    import chromedriver_autoinstaller
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium import webdriver
    # import undetected_chromedriver

# Install the latest version of chromedriver
# chromedriver_autoinstaller.install()

######################################################################

import argparse
parser = argparse.ArgumentParser(description="DIA Scraper")
parser.add_argument('--output_directory', type=str,
                    default=".", help='Output directory for CSV file')
parser.add_argument('--cp', type=str, default="08960",
                    help='Custom parameter cp')
args, unknown = parser.parse_known_args()

output_directory = args.output_directory
cp = args.cp
print(f"Postal code: {cp}")
now = time.localtime()
output_file = os.path.join(
    output_directory,
    f"dia_{cp}_{now.tm_year}_{now.tm_mon:02d}_{now.tm_mday:02d}.csv"
)
output_tmp_file = f"{output_file}.tmp"
print(f"Output file: {output_file}")

driver = None

products = []

######################################################################


def delete_output_files():
    try:
        os.remove(output_file)
        print(f"Deleted file: {output_file}")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error deleting {output_file}: {e}")

    try:
        os.remove(output_tmp_file)
        print(f"Deleted file: {output_tmp_file}")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error deleting {output_tmp_file}: {e}")


def export_product(file_name, product):
    # clean product data
    for key in product:
        if isinstance(product[key], str):
            product[key] = product[key].replace("\n", " ").replace(
                "\r", " ").replace("\t", " ").strip()

    # if no file exists, create it with headers
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding="utf-8") as csv_file:
            csv_file.write(
                "timestamp\tpostal_code\tid\tname\tprice\tis_on_promotion\turl\timage_file\t"
                "category_name_1\tcategory_id_1\tcategory_name_2\tcategory_id_2\t"
                "category_name_3\tcategory_id_3\tcategory_name_4\tcategory_id_4\t"
                "category_name_5\tcategory_id_5\nbrand\tean\tpromotion_1\tpromotion_2\n"
            )

    with open(file_name, "a", encoding="utf-8") as csv_file:
        csv_file.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t"
            f"{product.get('postal_code', '')}\t"
            f"{product.get('id', '')}\t"
            f"{product.get('name', '')}\t"
            f"{product.get('price', '')}\t"
            f"{str(product.get('is_on_promotion', False)).lower()}\t"
            f"{product.get('url', '')}\t"
            f"{product.get('image_file', '')}\t"
            f"{product.get('category_name_1', '')}\t"
            f"{product.get('category_id_1', '')}\t"
            f"{product.get('category_name_2', '')}\t"
            f"{product.get('category_id_2', '')}\t"
            f"{product.get('category_name_3', '')}\t"
            f"{product.get('category_id_3', '')}\t"
            f"{product.get('category_name_4', '')}\t"
            f"{product.get('category_id_4', '')}\t"
            f"{product.get('category_name_5', '')}\t"
            f"{product.get('category_id_5', '')}\t"
            f"{product.get('brand', '')}\t"
            f"{product.get('ean', '')}\t"
            f"{product.get('promotion_1', '')}\t"
            f"{product.get('promotion_2', '')}\n"
        )


def is_product_stored(product_id, product_name):
    for product in products:
        if product["name"] == product_name:
            if product["id"] == product_id:
                return True
    return False


def store_product(product_id, product_name, product_price, category1, category2, category3, category4, promotions, product_url, brand, ean, output_file):
    if is_product_stored(product_id, product_name):
        return False

    print(
        f"{product_id} - {product_name} - {product_price}{' - ' + brand if brand else ''}{' - ' + ean if ean else ''}{' - Promoted (' + promotions[0] + ')' if len(promotions) > 0 else ''}")
    products.append({
        "id": product_id,
        "name": product_name
    })
    export_product(output_file, {
        "postal_code": cp,
        "id": product_id,
        "name": product_name,
        "price": product_price,
        "is_on_promotion": True if len(promotions) > 0 else False,
        "url": product_url,
        "category_name_1": category1,
        "category_name_2": category2,
        "category_name_3": category3,
        "category_name_4": category4,
        "brand": brand,
        "ean": ean,
        "promotion_1": promotions[0] if len(promotions) > 0 else "",
        "promotion_2": promotions[1] if len(promotions) > 1 else "",
    })

    return True


def scrap_products(driver, category1, category2, output_file):
    # <li data-test-id="product-card-list-item" style="" class="product-card-list__item-container">
    productElements = driver.find_elements(
        By.XPATH, '//li[@data-test-id="product-card-list-item"]')
    print(f"{len(productElements)} products found")

    products_scrapped = 0
    for productElement in productElements:
        try:
            # <p class="search-product-card__product-name">Bacon en tiras Nuestra Alacena de Dia bandeja 2 x 100 g</p>
            product_name = productElement.find_element(
                By.XPATH, './/p[@class="search-product-card__product-name"]').get_attribute("innerText").strip()
        except Exception as e:
            # print("!!! Error finding product name")
            # print(e)
            continue

        try:
            # <p data-test-id="search-product-card-unit-price" class="search-product-card__active-price">1,84&nbsp;€</p>
            product_price = productElement.find_element(
                By.XPATH, './/p[@data-test-id="search-product-card-unit-price"]').get_attribute("innerText").strip()
        except Exception as e:
            # print("!!! Error finding product price")
            # print(e)
            continue

        try:
            # <a rel="external" href="/charcuteria-y-quesos/jamon-cocido-lacon-fiambres-y-mortadela/p/273750" data-test-id="search-product-card-image-url" class="search-product-card__product-image-link">
            product_url = productElement.find_element(
                By.XPATH, './/a[@data-test-id="search-product-card-image-url"]').get_attribute("href").strip()
            # href="/charcuteria-y-quesos/jamon-cocido-lacon-fiambres-y-mortadela/p/273750"
            product_id = product_url.split("/")[-1].strip()
        except Exception as e:
            # print("!!! Error finding product URL or ID")
            # print(e)
            continue

        try:
            promotions = []
            # <p class="product-special-offer__discount" data-test-id="product-special-offer-discount-percentage-discount">13% dto.</p>
            promotions.append(productElement.find_element(
                By.XPATH, './/p[@class="product-special-offer__discount"]').get_attribute("innerText").strip())
        except Exception as e:
            # print("!!! Error finding promotions")
            # print(e)
            pass

        if product_name and product_price:
            if store_product(product_id, product_name, product_price, category1, category2, "", "", promotions, product_url, "", "", output_file):
                products_scrapped += 1

    return products_scrapped


def reject_cookies(driver):
    try:
        cookies_dialog = driver.find_element(By.ID, 'onetrust-banner-sdk')
        button = cookies_dialog.find_element(
            By.ID, 'onetrust-reject-all-handler')
        button.click()
        time.sleep(2)
    except Exception as e:
        # print("!!! Error rejecting cookies:")
        # print(e)
        pass


def navigate(url):
    global driver
    last_exception = None
    for attempt in range(10):
        try:
            driver = create_driver()
            driver.get(url)
            time.sleep(10)
            reject_cookies(driver)
            set_cp(driver, cp)
            return
        except Exception as e:
            print(f"!!! Attempt {attempt+1}/10 failed in navigate: {e}")
            last_exception = e
            time.sleep(60)
    print("!!! Failed to create driver and navigate after 10 attempts.")
    if last_exception:
        raise last_exception


def find_category_1_elements(driver):
    try:
        # <ul data-test-id="categories-list" class="category-list">
        category1_elements_container = driver.find_element(
            By.XPATH, '//ul[@data-test-id="categories-list"]')
        category1_elements = category1_elements_container.find_elements(
            By.XPATH, "./li[@data-test-id='categories-list-element']")
        return category1_elements
    except Exception as e:
        print("!!! Error finding category 1 elements")
        print(e)
        exit(1)


def scrap_categories(products, output_file):
    global driver
    try:
        navigate("https://www.dia.es/")
        try:
            # <button data-test-id="mobile-category-button" class="category-button__mobile dia-icon-dehaze" aria-label="categories list menú button">
            menu_button = driver.find_element(
                By.XPATH, '//button[@data-test-id="mobile-category-button"]')
            driver.execute_script("arguments[0].click();", menu_button)
            time.sleep(2)
        except Exception as e:
            print("!!! Error finding menu button")
            print(e)
            exit(1)

        categories = []

        category1_elements = find_category_1_elements(driver)
        print(f"{len(category1_elements)} categories1 found")

        for category1_element_count in range(len(category1_elements)):
            try:
                category1_element = find_category_1_elements(
                    driver)[category1_element_count]

                category1_name = category1_element.find_element(
                    By.XPATH, './/span[@data-test-id="category-item-title"]').get_attribute("innerText").strip()
                category1_url = category1_element.find_element(
                    By.XPATH, './a').get_attribute("href")

                if category1_url.endswith("ofertas"):
                    continue

                print(f"Found category1: {category1_name}")

                clicable_item = category1_element.find_element(
                    By.XPATH, './/div[@data-test-id="category-item"]')
                driver.execute_script(
                    "arguments[0].scrollIntoView();", clicable_item)
                driver.execute_script("arguments[0].click();", clicable_item)
                time.sleep(1)

                category1_element = find_category_1_elements(
                    driver)[category1_element_count]

                # <ul data-test-id="sub-categories-list" class="sub-category-list" style="max-height: 420px;">
                category2_elements_container = category1_element.find_element(
                    By.XPATH, './/ul[@data-test-id="sub-categories-list"]')

                # <div data-test-id="sub-category-item" class="sub-category-item" data-v-5a72812c="">
                category2_elements = category2_elements_container.find_elements(
                    By.XPATH, "./div[@data-test-id='sub-category-item']")

                for category2_element in category2_elements:
                    try:
                        # <span data-test-id="sub-category-item-title" class="sub-category-item__text" data-v-5a72812c="">Todo verduras</span>
                        category2_name = category2_element.find_element(
                            By.XPATH, './/span[@data-test-id="sub-category-item-title"]').get_attribute("innerText").strip()
                        # <a data-test-id="sub-category-item-link" class="sub-category-item__link" href="/verduras/c/L104" data-v-5a72812c="">
                        category2_url = category2_element.find_element(
                            By.XPATH, "./a").get_attribute("href")

                        print(
                            f"Found category2: {category1_name} > {category2_name}")

                        categories.append({
                            "category1_url": category1_url,
                            "category1_name": category1_name,
                            "category2_url": category2_url,
                            "category2_name": category2_name
                        })

                    except Exception as e:
                        print("!!! Error finding category2 element")
                        # print(e)
                        continue

            except Exception as e:
                print("!!! Error finding category1 element")
                # print(e)
                continue

            category1_element_count += 1

        i = 0
        while i < len(categories):
            try:
                exception_count = 0
                category = categories[i]

                if category['category2_name'].startswith("Todo"):
                    i += 1
                    continue

                print(f"Navigating to {category['category2_url']}")
                navigate(category['category2_url'])

                print(f"\n**************************************************")
                print(f"Category1 {category['category1_name']}")
                print(f"Category2 {category['category2_name']}")
                print(f"Count {i + 1}/{len(categories)}")
                print(f"**************************************************\n")

                page = 0
                scroll = 0
                while True:
                    products_scrapped = scrap_products(
                        driver, category['category1_name'], category['category2_name'], output_file)

                    print(f"--------------------------------------------------")
                    print(f"Category1 {category['category1_name']}")
                    print(f"Category2 {category['category2_name']}")
                    print(f"Category count {i + 1}/{len(categories)}")
                    print(
                        f"{products_scrapped} products scrapped in page {page} - scroll {scroll}")
                    print(f"--------------------------------------------------")

                    scroll_position = driver.execute_script(
                        "return window.pageYOffset;")
                    # remote driver does not support Keys.PAGE_DOWN
                    driver.execute_script(
                        "window.scrollBy(0, window.innerHeight);")
                    time.sleep(1)
                    # remote driver does not support Keys.PAGE_DOWN
                    driver.execute_script(
                        "window.scrollBy(0, window.innerHeight);")
                    time.sleep(1)
                    new_scroll_position = driver.execute_script(
                        "return window.pageYOffset;")
                    if scroll_position == new_scroll_position:
                        print("No more scroll")
                        scroll = 0
                        break
                    else:
                        print("Scrolling down")
                        time.sleep(5)
                        scroll += 1

                i += 1
                exception_count = 0

            except Exception as e:
                print("!!! Error scrapping category.")
                print(e)
                exception_count += 1
                if exception_count > 10:
                    print("Too many exceptions, exiting")
                    exit(1)
                print(f"Retry scrapping category #{exception_count}")
                continue

        print(f"\n**************************************************")
        print(f"{len(products)} products exported to {output_file}")
        print(f"**************************************************")

    except Exception as e:
        print("!!! Error scrapping categories")
        print(e)
        exit(1)

######################################################################


def set_cp(driver, cp):
    try:
        # <div class="postal-code-button" data-test-id="postal-code-btn" icontext="08960">
        cp_input = driver.find_element(
            By.XPATH, '//div[@data-test-id="postal-code-btn"]')
        driver.execute_script("arguments[0].click();", cp_input)
        time.sleep(2)
        # <input id="input" type-input="number" inputmode="numeric" maxlength="5" data-test-id="postal-code-modal-input" class="postal-code__input" placeholder="Código postal">
        cp_input_field = driver.find_element(
            By.XPATH, '//input[@data-test-id="postal-code-modal-input"]')
        cp_input_field.clear()
        cp_input_field.send_keys(cp)
        time.sleep(2)
        # <button id="button" data-test-id="postal-code-modal-btn" class="postal-code__button-red" type="submit">
        cp_submit_button = driver.find_element(
            By.XPATH, '//button[@data-test-id="postal-code-modal-btn"]')
        driver.execute_script("arguments[0].click();", cp_submit_button)
        time.sleep(2)
    except Exception as e:
        print("!!! Error setting postal code")
        print(e)
        driver.save_screenshot(
            output_file.replace(".csv", ".error.set_cp.png"))
        exit(1)

######################################################################


def create_driver():
    try:
        global driver

        if driver is not None:
            driver.quit()
            driver = None

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--lang=es-ES")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--force-device-scale-factor=0.3")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        )
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-infobars")

        # Disable images to speed up loading and save BrightData bandwidth
        chrome_prefs = {
            "profile.default_content_setting_values": {
                "images": 2  # 2 significa que les imatges no es carregaran
            }
        }
        chrome_options.add_experimental_option("prefs", chrome_prefs)

        """
        webdriver_url = f"https://{os.environ['PROXY_USERNAME']}:{os.environ['PROXY_PASSWORD']}@{os.environ['PROXY_HOST']}:{os.environ['PROXY_PORT']}"
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        driver = webdriver.Remote(
            command_executor = webdriver_url,
            options = chrome_options
        )
        """

        driver = webdriver.Chrome(options=chrome_options)

        driver.set_window_size(1500, 2500)
        return driver
    except Exception as e:
        print(f"Error creating driver: {e}")
        raise e

######################################################################


delete_output_files()
scrap_categories(products, output_tmp_file)
os.rename(output_tmp_file, output_file)
driver.quit()
driver = None

######################################################################
