import json
import time
import requests
import pandas as pd
import tensorflow as tf
import simpleaudio as sa
from random import randrange
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

wave_obj = sa.WaveObject.from_wave_file('/Users/-------/Desktop/pythonProject/alert.wav')

# This loads the first page of 24 items.
WEBSITE = "https://www.website_name.com"
MAIN_PAGE = "/main_page"

options = webdriver.ChromeOptions()
# Incognito mode eliminates the caching issue.
options.add_argument("--incognito")
options.add_argument("--disable-blink-features")
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(options=options, executable_path='/Users/-------/Desktop/chromedriver2/chromedriver')

sort_page = pd.read_csv("price_scraper_page.csv", sep=";", index_col="Scrape Type")
sort_type = int(input("1 = Sort Type 1; 2 = Sort Type 2; 3 = Sort Type 3; 4 = Sort Type 4; 5 = Sort Type 5"))
max_page = 200
if sort_type == 1:
    PAGE_NUMBER = sort_page.loc["Sort Type 1"]["Page"]
    driver.get(WEBSITE + MAIN_PAGE + str(PAGE_NUMBER))
    time.sleep(randrange(30) / 10 + 3)
    input("Select Sort Type 1 from the dropdown menu and press enter to continue.")
    time.sleep(randrange(30)/10+3)
elif sort_type == 2:
    PAGE_NUMBER = sort_page.loc["Sort Type 2"]["Page"]
    MAIN_PAGE = "/Sort Type 2"
    max_page = 30
    driver.get(WEBSITE + MAIN_PAGE + str(PAGE_NUMBER))
    time.sleep(randrange(30) / 10 + 3)
elif sort_type == 3:
    PAGE_NUMBER = sort_page.loc["Sort Type 3"]["Page"]
    MAIN_PAGE = "/Sort Type 3"
    driver.get(WEBSITE + MAIN_PAGE + str(PAGE_NUMBER))
    time.sleep(randrange(30) / 10 + 3)
elif sort_type == 4:
    PAGE_NUMBER = sort_page.loc["Sort Type 4"]["Page"]
    MAIN_PAGE = "/Sort Type 4"
    driver.get(WEBSITE + MAIN_PAGE + str(PAGE_NUMBER))
    time.sleep(randrange(30) / 10 + 3)
else:
    PAGE_NUMBER = sort_page.loc["Sort Type 5"]["Page"]
    MAIN_PAGE = "/Sort Type 5"
    driver.get(WEBSITE + MAIN_PAGE + str(PAGE_NUMBER))
    time.sleep(randrange(30) / 10 + 3)


def normalize(item_data):
    asp_n = []
    mp_n = []
    q_n = []
    asp_f = []
    mp_f = []
    q_f = []
    i = 0
    while i < 180:
        asp_n.append(item_data[i])
        i += 1
        mp_n.append(item_data[i])
        i += 1
        q_n.append(item_data[i])
        i += 1
        asp_f.append(item_data[i])
        i += 1
        mp_f.append(item_data[i])
        i += 1
        q_f.append(item_data[i])
        i += 1
    max_price = max(max(asp_n), max(mp_n), max(asp_f), max(mp_f), .01)
    max_q = max(max(q_n), max(q_f), .01)
    i = 0
    while i < 180:
        item_data[i] = item_data[i] / max_price
        i += 1
        item_data[i] = item_data[i] / max_price
        i += 1
        item_data[i] = item_data[i] / max_q
        i += 1
        item_data[i] = item_data[i] / max_price
        i += 1
        item_data[i] = item_data[i] / max_price
        i += 1
        item_data[i] = item_data[i] / max_q
        i += 1
    return item_data


while PAGE_NUMBER < max_page:
    # This cycles through pages of items.
    driver.get(WEBSITE + MAIN_PAGE + str(PAGE_NUMBER))
    print("Processing page: " + str(PAGE_NUMBER))
    time.sleep(randrange(100)/10+3)

    # This produces a list of 24 item-page URLs per page.
    page_soup = BeautifulSoup(driver.page_source, 'html.parser')
    items = page_soup.find_all('div', {'class': 'search-result__content'})

    # This removes any item with a lowest listing of less than $0.25.
    less_items = []
    for item in items:
        try:
            check_price = float(
                item.find('span', {'class': 'inventory__price-with-shipping'}).text.replace('$', '').replace(',', ''))
            if check_price > .25 and check_price < 100:
                less_items.append(item)
        except:
            less_items.append(item)

    for item in less_items:
        item_URL = item.find('a', href=True)['href']
        URL = (WEBSITE + item_URL)

        try:
            driver.get(URL)
        except:
            print("!!Could NOT find " + URL)
        else:
            time.sleep(randrange(20)/10+4)
            URL_SPLIT = URL.split('?xid')[0]
            try:
                try:
                    NAME_FULL = driver.find_element(By.CLASS_NAME, "product-details__name").text.split(' - ')
                except:
                    time.sleep(randrange(80) / 10 + 8)
                    NAME_FULL = driver.find_element(By.CLASS_NAME, "product-details__name").text.split(' - ')
                NAME = NAME_FULL[0]
                SET = NAME_FULL[
                    len(NAME_FULL) - 1]  # Take last rather than second because of secret lair "flavor text" alts.

                first_item = driver.find_element(By.CLASS_NAME, "listing-item.product-details__listings-results")
                cheapest_item = float(first_item.find_element(By.CLASS_NAME, "listing-item__price").text.replace('$', ''))
                if first_item.find_element(By.TAG_NAME, "span").text == " Free Shipping ":
                    LOW = cheapest_item
                else:
                    cheapest_shipping = driver.find_element(By.CLASS_NAME, "shipping-messages__price").text
                    LOW = cheapest_item + float(cheapest_shipping.lower().replace('+ $', '').replace(' shipping', ''))
                MARKET = float(driver.find_element(By.CLASS_NAME, "product-details__price-guide").find_element(By.CLASS_NAME, "price").text.replace('$', ''))
                print(NAME)

                item_number = URL_SPLIT.split('/')[4]
                get_request_url = ("https://website-name.com/price/history/" + item_number + "?range=quarter")
                get_request = requests.get(get_request_url).text

                input_dict = json.loads(get_request)["result"]

                # This algorithm has to be run first to produce an estimate.
                model_array = []  # This is fed into the existing neural network to produce an estimate.

                i = 1
                for dates in input_dict:
                    variants = dates.get("variants")
                    if len(variants) == 2:
                        for variant in variants:
                            averageSalesPrice = variant["averageSalesPrice"]
                            marketPrice = variant["marketPrice"]
                            quantity = variant["quantity"]
                            model_array.append(float(averageSalesPrice))
                            model_array.append(float(marketPrice))
                            model_array.append(float(quantity))
                            i += 1
                    else:
                        for variant in variants:
                            averageSalesPrice = variant["averageSalesPrice"]
                            marketPrice = variant["marketPrice"]
                            quantity = variant["quantity"]
                            model_array.append(float(averageSalesPrice))
                            model_array.append(float(marketPrice))
                            model_array.append(float(quantity))
                            i += 1
                            averageSalesPrice = 0
                            marketPrice = 0
                            quantity = 0
                            model_array.append(float(averageSalesPrice))
                            model_array.append(float(marketPrice))
                            model_array.append(float(quantity))
                            i += 1

                model_input = normalize(model_array)
                model = tf.keras.models.load_model("neuralnet.model")
                prediction = model.predict([model_input])[0]
                print("The model predicts: " + str(prediction))

                if prediction[0] > .49:
                    yes_no = 0
                    print("This is a bad item. :(")
                elif prediction[2] > .52:
                    yes_no = 2
                    print("This is a great item!")
                # elif prediction[1] > .56:
                else:
                    yes_no = 1
                    print("This is a fine item.")
                # This was the code that allowed you to save inbetween items to add the the NN.
                # else:
                #     play_obj = wave_obj.play()
                #     yes_no = input("Enter 0 for bad item, 1 for neutral, 2 for a good looking chart.")
                #     print("--------------------------------------------")
                #
                #     # This outputs to training-set.csv. These two algorithms cannot be combined because it appends new
                #     # data to a dictionary with the score already input.
                #     output_dict = {'item Number': [item_number], 'Score': [yes_no]}
                #
                #     i = 1
                #     for dates in input_dict:
                #         variants = dates.get("variants")
                #         if len(variants) == 2:
                #             for variant in variants:
                #                 averageSalesPrice = variant["averageSalesPrice"]
                #                 marketPrice = variant["marketPrice"]
                #                 quantity = variant["quantity"]
                #                 output_dict["asp" + str(i)] = averageSalesPrice
                #                 output_dict["mp" + str(i)] = marketPrice
                #                 output_dict["q" + str(i)] = quantity
                #                 i += 1
                #         else:
                #             for variant in variants:
                #                 averageSalesPrice = variant["averageSalesPrice"]
                #                 marketPrice = variant["marketPrice"]
                #                 quantity = variant["quantity"]
                #                 output_dict["asp" + str(i)] = averageSalesPrice
                #                 output_dict["mp" + str(i)] = marketPrice
                #                 output_dict["q" + str(i)] = quantity
                #                 i += 1
                #                 averageSalesPrice = 0
                #                 marketPrice = 0
                #                 quantity = 0
                #                 output_dict["asp" + str(i)] = averageSalesPrice
                #                 output_dict["mp" + str(i)] = marketPrice
                #                 output_dict["q" + str(i)] = quantity
                #                 i += 1
                #
                #     # This adds an entry to the training set (only when it's a confusing one).
                #     df = pd.DataFrame(output_dict)
                #     df.to_csv('training_set.csv', mode='a', index=False, header=False, sep=";")

                # This adds the collected data to the buylist_names spreadsheet
                if MARKET > .5 and (int(yes_no) == 2 or (int(yes_no) == 1 and (LOW/MARKET)-1 > -.1)):
                    new_item = {'Link': [URL_SPLIT], 'item Name': [NAME], 'Set Name': [SET], 'Lowest': [LOW], 'Market': [MARKET], 'Rating': [yes_no]}
                    df = pd.DataFrame(new_item)
                    to_csv = df.to_csv('buylist_names.csv', mode='a', index=False, header=False, sep=';')

            except Exception as e:
                print(NAME + " did not load correctly, skipping to next item. More info:")
                print(e)

    PAGE_NUMBER += 1

    # This updates the csv file that tracks what page we're on.
    if sort_type == 1:
        sort_page = sort_page.drop("Sort Type 1")
        sort_page.loc["Sort Type 1"] = [PAGE_NUMBER]
        sort_page.to_csv("price_scraper_page.csv", mode='w', index=True, header=True, sep=";")
    elif sort_type == 2:
        sort_page = sort_page.drop("Sort Type 2")
        sort_page.loc["Sort Type 2"] = [PAGE_NUMBER]
        sort_page.to_csv("price_scraper_page.csv", mode='w', index=True, header=True, sep=";")
    elif sort_type == 3:
        sort_page = sort_page.drop("Sort Type 3")
        sort_page.loc["Sort Type 3"] = [PAGE_NUMBER]
        sort_page.to_csv("price_scraper_page.csv", mode='w', index=True, header=True, sep=";")
    elif sort_type == 4:
        sort_page = sort_page.drop("Sort Type 4")
        sort_page.loc["Sort Type 4"] = [PAGE_NUMBER]
        sort_page.to_csv("price_scraper_page.csv", mode='w', index=True, header=True, sep=";")
    else:
        sort_page = sort_page.drop("Sort Type 5")
        sort_page.loc["Sort Type 5"] = [PAGE_NUMBER]
        sort_page.to_csv("price_scraper_page.csv", mode='w', index=True, header=True, sep=";")
    # This navigates to the next page.
    driver.get(WEBSITE + MAIN_PAGE + str(PAGE_NUMBER))

driver.quit()
print("Thank you Aziz")
