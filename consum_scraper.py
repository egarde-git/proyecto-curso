import os
import re
import sys
import time
import subprocess

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
parser = argparse.ArgumentParser(description="Consum Scraper")
parser.add_argument('--output_directory', type=str,
                    default=".", help='Output directory for CSV file')
parser.add_argument('--cp', type=str, default="08001",
                    help='Custom parameter cp (postal code)')
args, unknown = parser.parse_known_args()

output_directory = args.output_directory
cp = args.cp
print(f"Postal code: {cp}")
now = time.localtime()
output_file = os.path.join(
    output_directory,
    f"consum_{cp}_{now.tm_year}_{now.tm_mon:02d}_{now.tm_mday:02d}.csv"
)
output_tmp_file = f"{output_file}.tmp"
print(f"Output file: {output_file}")

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
    # if no file exists, create it with headers
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding="utf-8") as csv_file:
            csv_file.write(
                "timestamp\tpostal_code\tid\tname\tprice\tis_on_promotion\turl\timage_file\t"
                "category_name_1\tcategory_id_1\tcategory_name_2\tcategory_id_2\t"
                "category_name_3\tcategory_id_3\tcategory_name_4\tcategory_id_4\t"
                "category_name_5\tcategory_id_5\n"
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
            f"{product.get('category_id_5', '')}\n"
        )


def store_product(product_id, product_name, product_price, category1, category2, category3, category4, is_on_promotion, product_url, brand, ean, output_file):
    for product in products:
        if product["name"] == product_name:
            if product["id"] == product_id:
                return False

    print(f"{product_id} - {product_name} - {product_price}{' - ' + brand if brand else ''}{' - ' + ean if ean else ''}{' - Promoted' if is_on_promotion else ''}")

    products.append({
        "id": product_id,
        "name": product_name
    })
    export_product(output_file, {
        "postal_code": cp,
        "id": product_id,
        "name": product_name,
        "price": product_price,
        "is_on_promotion": is_on_promotion,
        "url": product_url,
        "category_name_1": category1,
        "category_name_2": category2,
        "category_name_3": category3,
        "category_name_4": category4,
        "brand": brand,
        "ean": ean
    })

    return True

######################################################################


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


def navigate(driver, url, wait_for_xpath=None):
    print(f"Navigating to {url}")
    driver.get(url)
    if wait_for_xpath is not None:
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, wait_for_xpath))
            )
        except:
            time.sleep(5)
    else:
        time.sleep(5)
    reject_cookies(driver)


def scrap_page(driver, category1, category2, category3, category4, output_file):
    # <li data-test-id="product-card-list-item" style="" class="product-card-list__item-container">
    productElements = driver.find_elements(By.XPATH, '//cmp-widget-product')
    print(f"{len(productElements)} products found")

    products_scrapped = 0
    for productElement in productElements:
        try:
            # <h1 class="u-title-3">Bebida de Avena Mango y Plátano
            product_name = productElement.find_element(
                By.XPATH, './/h3[@class="u-title-3"]').get_attribute("innerText").strip()
        except Exception as e:
            print("!!! Error finding product name")
            print(e)
            continue

        try:
            # <p class="u-size--20">VIA NATURE</p>
            product_brand = productElement.find_element(
                By.XPATH, './/p[@class="u-size--20"]').get_attribute("innerText").strip()
        except Exception as e:
            # print("!!! Error finding product brand")
            # print(e)
            pass

        try:
            # <div class="product-info-price">
            #   <span class="product-info-price__offer ng-star-inserted">5,95&nbsp;€</span>
            #   <span class="product-info-price__price">4,95&nbsp;€</span>
            # </div>
            product_price = productElement.find_element(
                By.XPATH, './/span[@class="product-info-price__price"]').get_attribute("innerText").strip()
        except Exception as e:
            print("!!! Error finding product price")
            print(e)
            continue

        try:
            # <a class="u-no-link ng-tns-c3374034251-36" href="/es/p/bebida-de-avena-mango-y-platano/7457864">
            product_url = productElement.find_element(
                By.XPATH, './/a').get_attribute("href").strip()
            # https://tienda.consum.es/es/p/mozzarella-rallada-especial-pizza/7036155?_gl=1*1ekwfqy*_up*MQ..*_ga*ODY5MjY2NDEzLjE3NTA0OTYzODQ.*_ga_GB6KBC7QDN*czE3NTA0OTYzODQkbzEkZzAkdDE3NTA0OTYzODQkajYwJGwwJGg4NjYyNTI5OTU.
            product_id = product_url.split("/")[-1].split("?")[0]
        except Exception as e:
            # print("!!! Error finding product URL or ID")
            # print(e)
            pass

        try:
            # <div class="product-info-promotions ng-star-inserted">
            productElement.find_element(
                By.XPATH, './/div[contains(@class, "product-info-promotions")]')
            is_on_promotion = True
        except Exception as e:
            # print("!!! Error finding promotion element:")
            # print(e)
            is_on_promotion = False

        if product_name and product_price:
            if store_product(product_id, product_name, product_price, category1, category2, category3, category4, is_on_promotion, product_url, product_brand, "", output_file):
                products_scrapped += 1

    return products_scrapped


def scrap_categories(driver):
    try:
        final_categories = []

        navigate(driver, "https://tienda.consum.es/es")
        try:
            # <button data-test-id="mobile-category-button" class="category-button__mobile dia-icon-dehaze" aria-label="categories list menú button">
            menu_button = driver.find_element(
                By.XPATH, '//div[@class="menu-button"]')
            driver.execute_script("arguments[0].click();", menu_button)
            time.sleep(2)
        except Exception as e:
            print("!!! Error finding menu button")
            print(e)
            exit(1)

        ### CATEGORIES 1 ###

        category1_elements = driver.find_elements(
            By.XPATH, "//cmp-panel//li[contains(@class, 'ng-star-inserted')]")
        print(f"{len(category1_elements)} categories1 found")

        categories1 = []
        for category1_element in category1_elements:
            try:
                # <a class="element-list__link ng-star-inserted element-list__link--active" href="https://tienda.consum.es/es/c/despensa/2811">
                category1_element = category1_element.find_element(
                    By.XPATH, './/a')

                category1_name = category1_element.text.strip()
                if category1_name.startswith("Navidad"):
                    continue
                if category1_name.startswith("Momentos Consum"):
                    continue
                if category1_name.startswith("Recetas"):
                    continue
                if category1_name.startswith("Folleto Online"):
                    continue
                if category1_name.startswith("¡Novedades!"):
                    continue
                if category1_name.startswith("Nuestras marcas"):
                    continue

                categories1.append({
                    "url": category1_element.get_attribute("href"),
                    "category1_name": category1_name
                })
                print(
                    f"Non final category 1: {categories1[-1]['category1_name']}")
            except Exception as e:
                print(e)
                continue

        ### CATEGORIES 2 ###

        categories2 = []
        for category1 in categories1:
            try:
                navigate(driver, category1['url'],
                         '//div[@id="grid-filter-categories"]//a')

                # <div id="grid-filter-categories" class="ng-star-inserted">...
                # <a class="u-title u-pointer flex-grow-1" href="https://tienda.consum.es/es/c/bebidas/aguas/2482">Aguas</a>
                category2_elements = driver.find_elements(
                    By.XPATH, '//div[@id="grid-filter-categories"]//a')
                print(f"{len(category2_elements)} categories2 found")
                for category2_element in category2_elements:
                    try:
                        categories2.append({
                            "url": category2_element.get_attribute("href"),
                            "category1_name": category1.get("category1_name", ""),
                            "category2_name": category2_element.text
                        })
                        print(
                            f"Non final category 2: {categories2[-1]['category1_name']} > {categories2[-1]['category2_name']}")
                    except Exception as e:
                        print(e)
                        continue
            except Exception as e:
                print(e)
                continue

        ### CATEGORIES 3 ###

        categories3 = []
        for category2 in categories2:
            try:
                navigate(driver, category2['url'],
                         '//div[@id="grid-filter-categories"]//a')

                # <div id="grid-filter-categories" class="ng-star-inserted">...
                # <a class="u-title u-pointer flex-grow-1" href="https://tienda.consum.es/es/c/bebidas/aguas/agua-con-gas/1691">Agua con gas</a>
                category3_elements = driver.find_elements(
                    By.XPATH, '//div[@id="grid-filter-categories"]//a')
                print(f"{len(category3_elements)} categories3 found")

                # check if category3_elements[0] are actually category 2
                if len(category3_elements) > 0 and re.fullmatch(r".*/c/([^/]+/){2}[^/]+", category3_elements[0].get_attribute("href")):
                    final_categories.append({
                        "url": category2.get("url", ""),
                        "category1_name": category2.get("category1_name", ""),
                        "category2_name": category2.get("category2_name", ""),
                        "category3_name": "",
                        "category4_name": ""
                    })
                    print(
                        f"Final category 2: {final_categories[-1]['category1_name']} > {final_categories[-1]['category2_name']}")
                    continue

                for category3_element in category3_elements:
                    try:
                        categories3.append({
                            "url": category3_element.get_attribute("href"),
                            "category1_name": category2.get("category1_name", ""),
                            "category2_name": category2.get("category2_name", ""),
                            "category3_name": category3_element.text,
                            "category4_name": ""
                        })
                        print(
                            f"Non final category 3: {categories3[-1]['category1_name']} > {categories3[-1]['category2_name']} > {categories3[-1]['category3_name']}")
                    except Exception as e:
                        print(e)
                        continue
            except Exception as e:
                print(e)
                continue

        ### CATEGORIES 4 ###

        for category3 in categories3:
            try:
                navigate(driver, category3['url'])

                # <div id="grid-filter-categories" class="ng-star-inserted">...
                # <a class="u-title u-pointer flex-grow-1" href="https://tienda.consum.es/es/c/bebidas/aguas/agua-con-gas/1691">Agua con gas</a>
                category4_elements = driver.find_elements(
                    By.XPATH, '//div[@id="grid-filter-categories"]//a')
                print(f"{len(category4_elements)} categories4 found")

                # check if category4_elements[0] are actually category 3
                if len(category4_elements) > 0 and re.fullmatch(r".*/c/([^/]+/){3}[^/]+", category4_elements[0].get_attribute("href")):
                    final_categories.append({
                        "url": category3.get("url", ""),
                        "category1_name": category3.get("category1_name", ""),
                        "category2_name": category3.get("category2_name", ""),
                        "category3_name": category3.get("category3_name", ""),
                        "category4_name": ""
                    })
                    print(
                        f"Final category 3: {final_categories[-1]['category1_name']} > {final_categories[-1]['category2_name']} > {final_categories[-1]['category3_name']}")
                    continue

                for category4_element in category4_elements:
                    try:
                        final_categories.append({
                            "url": category4_element.get_attribute("href"),
                            "category1_name": category3.get("category1_name", ""),
                            "category2_name": category3.get("category2_name", ""),
                            "category3_name": category3.get("category3_name", ""),
                            "category4_name": category4_element.text
                        })
                        print(
                            f"Final category 4: {final_categories[-1]['category1_name']} > {final_categories[-1]['category2_name']} > {final_categories[-1]['category3_name']} > {final_categories[-1]['category4_name']}")
                    except Exception as e:
                        print(e)
                        continue

            except Exception as e:
                print(e)
                continue

    except Exception as e:
        print(e)

    return final_categories


def scrap_products(driver, categories, products, output_file):
    try:
        category_count = 0
        for category in categories:
            try:
                category_count += 1

                print(f"\n**************************************************")
                navigate(driver, category['url'], '//cmp-widget-product')
                print(f"Category1 {category['category1_name']}")
                print(f"Category2 {category['category2_name']}")
                print(f"Category3 {category['category3_name']}")
                print(f"Category4 {category['category4_name']}")
                print(f"Count {category_count}/{len(categories)}")
                print(f"--------------------------------------------------")

                page = 0
                while True:
                    products_scrapped = scrap_page(
                        driver, category['category1_name'], category['category2_name'], category['category3_name'], category['category4_name'], output_file)

                    print(f"--------------------------------------------------")
                    print(f"{products_scrapped} products scrapped in page {page}")
                    print(f"--------------------------------------------------")

                    try:
                        # <div id="paginator-dropdown" class="paginator-dropdown">
                        pagination_row = driver.find_element(
                            By.ID, 'paginator-dropdown')
                        # If the next page button is not found, except
                        # <a routerlink="./" class="next-page" href="https://tienda.consum.es/">
                        pagination_row.find_element(
                            By.XPATH, './/a[@class="next-page"]')
                        # <cmp-icon id="paginator-dropdown-icon-right" name="icon-right" class="d-flex u-cursor--pointer">
                        next_page_button = pagination_row.find_element(
                            By.XPATH, './/cmp-icon[@id="paginator-dropdown-icon-right"]')
                        driver.execute_script(
                            "arguments[0].click();", next_page_button)
                        time.sleep(5)
                        print("Next page button found")
                        page += 1
                    except Exception as e:
                        print("No next page button found")
                        break

            except Exception as e:
                print("!!! Error scrapping category")
                # print(e)
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
        navigate(driver, "https://tienda.consum.es/es")
        # <span class="select-zipCode__label--text ng-star-inserted">Indica zona de compra</span>
        cp_input = driver.find_element(
            By.XPATH, '//span[contains(@class, "select-zipCode")]')
        driver.execute_script("arguments[0].click();", cp_input)
        time.sleep(2)
        # find <input type="text" autofocus="" class="field-zip-input u-text--regular u-size--16 ng-pristine ng-valid ng-touched">
        cp_input_field = driver.find_element(
            By.XPATH, '//input[contains(@class, "field-zip-input")]')
        cp_input_field.clear()
        cp_input_field.send_keys(cp)
        time.sleep(2)
        # <button id="shipping-address-panel--btn-accept-address" translate="" class="btn btn-primary btn-custom u-height--50 u-rounded-40 page-not-found__button step-button-main w-100 u-size--18 ng-tns-c2007936807-33 ng-star-inserted"> Confirmar dirección </button>
        cp_submit_button = driver.find_element(
            By.ID, 'shipping-address-panel--btn-accept-address')
        driver.execute_script("arguments[0].click();", cp_submit_button)
        time.sleep(2)
    except Exception as e:
        print("!!! Error setting postal code")
        print(e)
        driver.save_screenshot(
            output_file.replace(".csv", ".error.set_cp.png"))
        exit(1)

######################################################################


delete_output_files()

products = []

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--lang=es-ES")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--window-size=1500,1500")
chrome_options.add_argument("--force-device-scale-factor=0.5")
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
)
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-infobars")

# Disable images to speed up loading
chrome_prefs = {
    "profile.default_content_setting_values": {
        "images": 2  # 2 significa que les imatges no es carregaran
    }
}
chrome_options.add_experimental_option("prefs", chrome_prefs)

driver = webdriver.Chrome(options=chrome_options)
# driver = undetected_chromedriver.Chrome(options=chrome_options)

set_cp(driver, cp)
categories = scrap_categories(driver)
scrap_products(driver, categories, products, output_tmp_file)
os.rename(output_tmp_file, output_file)

driver.quit()
driver = None

######################################################################
