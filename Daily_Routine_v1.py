import time
import schedule
import pandas as pd
import datetime as dt
import simpleaudio as sa
from random import randrange
from selenium import webdriver
from datetime import date, datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options

wave_obj = sa.WaveObject.from_wave_file('/Users/-------/Desktop/pythonProject/alert.wav')

WEBSITE = "https://store.the_website.com"
purchases_INVENTORY = "/admin/purchases/inventory"
purchases_PAGE = "/admin/purchases/pricing"
PRICING_PAGE = "/admin/Pricing"
ORDERS_PAGE = "/admin/orders/orderlist"

chrome_driver = '/Users/-------/Desktop/pythonProject/chromedriver'
driver = webdriver.Chrome(chrome_driver, options=options)

input("Press enter once logged in...")


# This clears the search field and Group Name dropdown menu.
def page_reset(full_or_my_catalog):
    # This makes sure there is no text in the search area or item Group selected.
    print("startring the loop")
    time.sleep(randrange(30) / 10 + 1)
    search = driver.find_element(By.ID, "Search")
    search.clear()
    print("cleared existing searches")
    Group_selector = Select(driver.find_element(By.ID, "GroupNameId"))
    Group_selector.select_by_visible_text("All Group Names")
    print("cleared Group names")

    # This makes sure the advanced filters section isn't already open because otherwise it will shut.
    try:
        driver.find_element(By.ID, "catalogFullthe_website").click()
        print("advanced filters already open")
    except:
        # This opens the advanced filters section.
        advanced = driver.find_element(By.CLASS_NAME, "basic-filters")
        buttons = advanced.find_elements(By.TAG_NAME, "input")
        buttons[2].click()
        time.sleep(1)

    if full_or_my_catalog == "full_catalog":
        driver.find_element(By.ID, "catalogFullthe_website").click()
        time.sleep(1)
        print("selected full catalog")
    else:
        # This selects only my catalog.
        driver.find_element(By.ID, "catalogMineOnly").click()
        time.sleep(1)

        # This selects the subsection of my catalog that's active. It's different on the purchases and pricing page.
        try:
            driver.find_element(By.ID, "purchasesMineOnly").click()
        except:
            driver.find_element(By.ID, "stockTypeInStock").click()
        time.sleep(10)
        print("selected my catalog")

    # This enters those terms and submits the query.
    items = driver.find_element(By.ID, "pagerTop")
    items = Select(items.find_element(By.TAG_NAME, "select"))
    items.select_by_visible_text("500")
    time.sleep(randrange(50) / 10 + 5)
    print("clicked 500 items to display")

    search_run = 0
    while search_run == 0:
        try:
            advanced = driver.find_element(By.CLASS_NAME, "basic-filters")
            buttons = advanced.find_elements(By.TAG_NAME, "input")
            buttons[1].click()
            search_run += 1
        except:
            print("Waiting another 5 seconds for Search button to load.")
            time.sleep(randrange(50) / 10 + 5)

    while not driver.find_elements(By.CLASS_NAME, "product-listing"):
        print("Waiting another 5 seconds for page to load.")
        time.sleep(randrange(50) / 10 + 5)


# This scans each line of a purchases page and updates the pricing based on prices in purchases_bids.
def purchases_price_updater(listings, comp_sheet, new_or_existing):
    profit = 0
    cost = 0
    items = 0
    itemScore = 0
    price_updates = 0
    profit_low = 0
    margin_low = 0
    too_expensive = 0

    for line in listings:
        try:
            market_price = 0.00
            # We get the purchases item name.
            name_area = line.find_element(By.CLASS_NAME, "product-listing_name")
            purchases_item_name = name_area.find_element(By.TAG_NAME, "a").text
            # We get the purchases Group name.
            meta_data = line.find_element(By.CLASS_NAME, "product-listing_meta")
            metas = meta_data.find_elements(By.TAG_NAME, "span")
            purchases_Group_name = metas[0].text
            # We get the purchases condition.
            purchases_condition = metas[4].text

            # We set the market_price equal to the lowest listing plus shipping.
            for variants in comp_sheet:
                if variants[0] == purchases_item_name and variants[1] == purchases_Group_name and variants[2] == purchases_condition:
                    market_price = float(variants[3])
                    if new_or_existing == "new":
                        itemScore = variants[5]
                        print("This is a new item with a score of: " + str(itemScore))
                    else:
                        itemScore = variants[4]
            if itemScore == 2:
                return_on_investment = 1.20
            else:
                return_on_investment = 1.30

            # This finds the current high purchases asking price.
            purchases_high_area = line.find_element(By.CLASS_NAME, "product-listing_market-price")
            metas_BH = purchases_high_area.find_elements(By.TAG_NAME, "span")
            purchases_high = float(metas_BH[1].text)

            # This checks to see if we already have a purchases asking price entered.
            bid = line.find_elements(By.TAG_NAME, "input")
            try:
                purchases_bid = float((bid[len(bid) - 2].get_attribute("value")).replace('$', ''))
            except:
                purchases_bid = 0.00

            new_bid = round((purchases_high + 0.01), 2)
            pending_purchase = int(line.find_element(By.CLASS_NAME, "product-listing__pending-qty").text)

            # This accounts for the extra commission paid on items less than $1.
            if purchases_high < 1:
                purchases_cost = purchases_high + ((1 - purchases_high) * .1)
            else:
                purchases_cost = purchases_high

            # This estimates what we will get for an item after fees.
            # the_website fee is 8.95% plus $1.09 for shipping.
            # Credit item fee is 2.5% plus $0.30.
            if market_price > 3:
                item_value = (market_price * .8855) - 1.39
            else:
                item_value = market_price * .5

            # This checks all our conditions, and if they're met, sets the QTY to two greater than pending QTY.
            bid[len(bid) - 1].clear()
            if item_value - (purchases_cost * 1.1) < 0.75:
                print("!!profit too low: $" + str(round(item_value - purchases_cost * 1.1, 2)))
                profit_low += 1
            elif item_value / (purchases_cost * 1.1) < return_on_investment:
                print("!!margin too low: " + str(
                    round((item_value / (purchases_cost * 1.1) - 1) * 100, 2)) + "%")
                margin_low += 1
            elif purchases_cost > 100:
                print("!!too rich for my blood!!")
                too_expensive += 1
            else:
                bid[len(bid) - 1].send_keys(pending_purchase + 2)
                profit += item_value - (purchases_cost * 1.1)
                cost += purchases_cost * 1.1
                items += 1
                # print("$trong profits,")

            # This checks to see if we are currently bidding on any number of items.
            try:
                purchases_quantity = float((bid[len(bid) - 1].get_attribute("value")))
            except:
                purchases_quantity = 0

            # This sets the price we're willing to pay, if we're willing to bid on an item.
            if purchases_high != purchases_bid and purchases_quantity > pending_purchase:
                bid[len(bid) - 2].clear()
                bid[len(bid) - 2].send_keys(new_bid)
                print("price updated to: $" + str(new_bid))
                price_updates += 1
                # This is updating the purchases_bids.csv.
                if new_or_existing == "new":
                    list_updater(purchases_item_name, purchases_Group_name, purchases_condition, market_price, itemScore,
                                 "purchases_bids.csv")

        except Exception as e:
            print("Bad line, cause of error:")
            print(e)
            bid = line.find_elements(By.TAG_NAME, "input")
            bid[len(bid) - 1].clear()

    # This prints the average profit for the list of items evaluated, and avoids div0 errors.
    try:
        avg_margin = round(profit / cost, 2) * 100
        avg_profit = round(profit / items, 2)
    except:
        avg_margin = 0
        avg_profit = 0

    print("--------------")
    print(str(items) + " bids on items.")
    print("Average profit = $" + str(avg_profit))
    print("Average margin = " + str(avg_margin) + "%")
    print(str(price_updates) + " prices updated.")
    print(str(profit_low) + " items with low profits.")
    print(str(margin_low) + " items with low margins.")
    print(str(too_expensive) + " items that are too expensive.")


# This scans each line of the pricing page and updates the pricing based on current market prices.
def price_downdater(listings):
    for line in listings:
        # First we identify the item name, lowest listing, market price, and our current asking price.)
        name_area = line.find_element(By.CLASS_NAME, "product-listing_name")
        item_name = name_area.find_element(By.TAG_NAME, "a").text
        try:  # This is here because sometimes the_website doesn't report the lowest price.
            lowest_listing = line.find_element(By.CLASS_NAME, "product-listing_lowest-listing")
            price_L = lowest_listing.find_elements(By.TAG_NAME, "span")
            lowest_price = round(float(price_L[1].text) + float(price_L[2].text), 2)
        except:
            print("!!!the_website not showing a lowest listing, setting value to zero!!!")
            lowest_price = 0

        # This whole block of code may be vestigial.
        # try:  # Apparently the_website also sometimes doesn't have a market price listed.
        #     market_listing = line.find_element(By.CLASS_NAME, "product-listing_market-price")
        #     price_M = market_listing.find_elements(By.TAG_NAME, "span")
        #     market_price = round(float(price_M[1].text) - 0.99, 2)
        # except:
        #     print("!!!the_website  not showing a market price, setting value to zero!!!")
        #     market_price = 0

        # This is finding at the current asking price
        ask = line.find_elements(By.TAG_NAME, "input")
        purchases_ask = round(float((ask[len(ask) - 2].get_attribute("value")).replace('$', '')), 2)

        if purchases_ask < 0.80:
            print(item_name + ": Price already at minimum.")
        elif purchases_ask <= lowest_price:
            purchases_ask -= max(.01, round(purchases_ask * .001, 2))
            print(item_name + ": Already the lowest ask, price decreased 0.1%.")
        else:
            purchases_ask -= max(.01, round(purchases_ask * .0050, 2))
            print(item_name + ": Price decreased 0.5%, to " + str(round(purchases_ask, 2)))

        ask[len(ask) - 2].clear()
        ask[len(ask) - 2].send_keys(round(purchases_ask, 2))  # Remove the round() if you figure out the issue.


# This runs the price updater/downdater function, and cycles to the next page when possible.
def pricelist_updater(purchases_or_inventory):
    print("******RUNNING THE PRICELIST_UPDATER FUNCTION*******")
    is_next = 1
    first_loop = 0

    while is_next == 1:
        if purchases_or_inventory == "purchases":
            if first_loop == 0:
                driver.get(WEBSITE + purchases_PAGE)
                time.sleep(randrange(50) / 10 + 5)
                page_reset('my_catalog')
                first_loop += 1
            pricelist_updater_listings = driver.find_elements(By.CLASS_NAME, "product-listing")
            purchases_bids_array = []
            bid_list = pd.read_csv("purchases_bids.csv", sep=";")
            i = 0
            while i < len(bid_list):
                purchases_bids_array.append([bid_list.iloc[i]["item Name"], bid_list.iloc[i]["Group Name"], bid_list.iloc[i]["Condition"], bid_list.iloc[i]["Price"], bid_list.iloc[i]["Score"]])
                i += 1
            purchases_price_updater(pricelist_updater_listings, purchases_bids_array, "existing")  # This runs the function that updates all the prices.
        if purchases_or_inventory == "inventory":
            if first_loop == 0:
                print("Navigating to pricing page.")
                driver.get(WEBSITE + PRICING_PAGE)
                time.sleep(randrange(50) / 10 + 5)
                print("Running page reset function.")
                page_reset('my_catalog')
                first_loop += 1
            print("Scraping listings.")
            while not driver.find_elements(By.CLASS_NAME, "product-listing"):
                print("Waiting another 5 seconds for page to load.")
                time.sleep(randrange(50) / 10 + 5)
            pricelist_updater_listings = driver.find_elements(By.CLASS_NAME, "product-listing")
            print("Runinng downdater function")
            price_downdater(pricelist_updater_listings)

        # This section submits the changes.
        exits = driver.find_element(By.TAG_NAME, "pricing-actions")
        buttons = exits.find_elements(By.TAG_NAME, "input")
        buttons[len(buttons) - 1].send_keys(Keys.ENTER)
        print("**submitting updates, waiting 30 seconds**")
        time.sleep(randrange(50) / 10 + 27)
        if not buttons[len(buttons) - 1].is_enabled():
            print("**page not ready after 45 seconds... waiting additional 60 seconds**")
            time.sleep(randrange(100) / 10 + 55)

        # This section checks if there's another page.
        # If so it clicks it. If not it ends the loop.
        nav = driver.find_element(By.CLASS_NAME, "pager")
        next_page = nav.find_elements(By.TAG_NAME, "button")
        if next_page[len(next_page) - 2].is_enabled():
            next_page[len(next_page) - 2].send_keys(Keys.ENTER)
            print("**navigating to next page, waiting 10 seconds**")
            time.sleep(randrange(50) / 10 + 15)

        else:
            is_next += 1


# This function finds a matching item in the list "lu_csv", deletes it, and replaces it with updated data.
# This function is ONLY used by new_item_helper.
def list_updater(lu_name, lu_Group, lu_condition, lu_price, lu_score, lu_csv):
    bids = pd.read_csv(lu_csv, sep=";")
    lu_item_names = bids['item Name'].tolist()
    lu_Group_names = bids['Group Name'].tolist()
    lu_conditions = bids['Condition'].tolist()
    lu_date = date.today()
    target_index = -1

    # This loop removes a matching line from the csv so it can be updated.
    for lu_names in lu_item_names:
        list_index = lu_item_names.index(lu_names)
        if lu_names == lu_name and lu_Group_names[list_index] == lu_Group and lu_conditions[list_index] == lu_condition:
            target_index = list_index
            print("Match found for " + lu_name + " from " + lu_Group + " in condition " + lu_condition)

    if target_index > -1:
        bids = bids.drop([target_index])
        print("Line deleted in " + lu_csv)

    new_bid_line = [lu_name, lu_Group, lu_condition, round(lu_price, 2), lu_date, lu_score]
    bids.loc[len(bids) + 1] = new_bid_line
    bids.to_csv(lu_csv, mode='w', index=False, header=True, sep=';')
    print("New line added to " + lu_csv)


# this function takes the list of items in purchases_names.csv, bids on good items, and updates purchases_bids.csv.
def new_item_helper(quantity):
    print("******RUNNING THE NEW_item_HELPER FUNCTION******")

    data = pd.read_csv("purchases_names.csv", sep=";")
    item_names = data['item Name'].tolist()
    Group_names = data['Group Name'].tolist()
    item_scores = data['Rating'].tolist()
    print("Data extracted.")
    item_scan_counter = quantity

    for name in item_names:
        try:
            most_recent_mint_low = 0
            most_recent_light_low = 0
            time.sleep(randrange(40) / 10 + 2)
            driver.get(WEBSITE + PRICING_PAGE)
            time.sleep(randrange(40) / 10 + 2)

            # This extracts the data
            item_position = item_names.index(name)
            # Finding the itemGroup name is complicated by items that have parenthesis in the name.
            itemGroup = Group_names[item_position].split(" (")
            if len(itemGroup) > 2:
                itemGroup = itemGroup[0] + " (" + itemGroup[1]
            else:
                itemGroup = itemGroup[0]

            itemScore = item_scores[item_position]
            print("Scraping lowest price data for " + name + " from the Group " + itemGroup)

            # This Groups items per page to 100.
            if item_position < 3:
                # This opens the advanced filters section.
                advanced = driver.find_element(By.CLASS_NAME, "basic-filters")
                buttons = advanced.find_elements(By.TAG_NAME, "input")
                buttons[2].click()
                time.sleep(1)

                # This selects only my catalog.
                driver.find_element(By.ID, "catalogFullthe_website").click()
                time.sleep(1)

                items = driver.find_element(By.ID, "pagerTop")
                items = Select(items.find_element(By.TAG_NAME, "select"))
                items.select_by_visible_text("100")
                time.sleep(20)

            while not driver.find_element(By.ID, "GroupNameId"):
                print("Waiting another 5 seconds for page to load.")
                time.sleep(5)

            # This selects the item Group from the dropdown menu
            Group_selector = Select(driver.find_element(By.ID, "GroupNameId"))
            Group_selector.select_by_visible_text(itemGroup)

            while not driver.find_element(By.ID, "Search"):
                print("Waiting another 5 seconds for page to load.")
                time.sleep(5)

            # This inputs the name of the item and submits the inquiry
            search = driver.find_element(By.ID, "Search")
            search.clear()
            search.send_keys(name)
            search.send_keys(Keys.ENTER)
            time.sleep(randrange(40) / 10 + 2)

            while not driver.find_elements(By.CLASS_NAME, "product-listing"):
                print("Waiting another 5 seconds for page to load.")
                time.sleep(5)

            listings = driver.find_elements(By.CLASS_NAME, "product-listing")

            # This will save the lowest listing price info to an array.
            lowest_listings = []
            for line in listings:
                # This gets the full item name for each line.
                name_area = line.find_element(By.CLASS_NAME, "product-listing__name")
                line_item_name = name_area.find_element(By.TAG_NAME, "a").text

                # This gets the item condition for each line.
                meta_data = line.find_element(By.CLASS_NAME, "product-listing__meta")
                metas = meta_data.find_elements(By.TAG_NAME, "span")
                line_condition = metas[4].text

                # This gets the lowest price.
                try:
                    meta_data = line.find_element(By.CLASS_NAME, "product-listing__lowest-listing")
                    prices = meta_data.find_elements(By.TAG_NAME, "span")
                    line_price = float(prices[1].text) + float(prices[2].text)
                except:
                    line_price = 0

                if line_condition == "Near Mint" or line_condition == "Near Mint Foil":
                    most_recent_mint_low = line_price

                if line_condition == "Lightly Played" or line_condition == "Lightly Played Foil":
                    line_price = min(line_price, most_recent_mint_low * .93)
                    most_recent_light_low = line_price

                if line_condition == "Moderately Played" or line_condition == "Moderately Played Foil":
                    if line_price == 0:
                        line_price = most_recent_light_low * .93
                    else:
                        line_price = min(line_price, most_recent_light_low * .93)
                the_date = str(date.today())
                lowest_listings.append([line_item_name, itemGroup, line_condition, line_price, the_date, itemScore])

            # This is now navigating to the purchases page for the same item.
            driver.get(WEBSITE + purchases_PAGE)
            time.sleep(randrange(40) / 10 + 2)

            # This sets items per page to 100.
            if item_position < 3:
                # This opens the advanced filters section.
                advanced = driver.find_element(By.CLASS_NAME, "basic-filters")
                buttons = advanced.find_elements(By.TAG_NAME, "input")
                buttons[2].click()
                time.sleep(1)

                # This selects only my catalog.
                driver.find_element(By.ID, "catalogFullthe_website").click()
                time.sleep(1)

                items = driver.find_element(By.ID, "pagerTop")
                items = Select(items.find_element(By.TAG_NAME, "select"))
                items.select_by_visible_text("100")
                time.sleep(20)

            # This selects the item Group from the dropdown menu
            Group_selector = Select(driver.find_element(By.ID, "GroupNameId"))
            Group_selector.select_by_visible_text(itemGroup)

            # This inputs the name of the item and submits the inquiry
            search = driver.find_element(By.ID, "Search")
            search.clear()
            search.send_keys(name)
            search.send_keys(Keys.ENTER)
            time.sleep(randrange(40) / 10 + 2)

            new_item_listings = driver.find_elements(By.CLASS_NAME, "product-listing")
            while len(new_item_listings) == 0:
                print("Waiting extra time for page to load, length: " + str(len(new_item_listings)))
                time.sleep(2)
                new_item_listings = driver.find_elements(By.CLASS_NAME, "product-listing")

            # THIS IS MOVING TO THE purchases_PRICE_UPDATER FUNCTION
            purchases_price_updater(new_item_listings, lowest_listings, "new")

            # this will find the first element called 'pricing-actions'
            exits = driver.find_element(By.TAG_NAME, "pricing-actions")
            buttons = exits.find_elements(By.TAG_NAME, "input")
            # this will find the last input in pricing-actions, which is the close button
            buttons[len(buttons) - 1].send_keys(Keys.ENTER)
            time.sleep(1)

            # This refreshes the purchases_names.csv file, and deletes the first entry.
            data = pd.read_csv("purchases_names.csv", sep=";")
            data = data.iloc[1:]
            data.to_csv('purchases_names.csv', mode='w', index=False, header=True, sep=";")

            # This is HOPEFULLY waiting for the changes to be saved.
            while not driver.find_element(By.ID, "Search"):
                print("Waiting another 5 seconds for page to load.")
                time.sleep(5)

        except Exception as e:
            print(e)
            wave_obj.play()
            input("New item scanner stuck. Resolve issue and press ENTER to continue:")

        item_scan_counter -= 1
        print(str(item_scan_counter) + " items left to scan.")
        if item_scan_counter == 0:
            break


# This function deletes old lines from purchases_bids.csv.
def purchases_bids_cleanup():
    date_today = date.today()
    purchases_bid_list = pd.read_csv("purchases_bids.csv", sep=";")

    # This adds any items older than "delta" to a list to be removed.
    old_items = []
    i = 0
    while i < len(purchases_bid_list):
        item_date = date.fromisoformat(purchases_bid_list.iloc[i]["Date"])
        delta = int((date_today - item_date).days)
        if delta > 11:
            old_items.append(i)
        i += 1

    purchases_bid_list = purchases_bid_list.drop(old_items)
    purchases_bid_list.to_csv('purchases_bids.csv', mode='w', index=False, header=True, sep=";")


# This function adds new inventory from Purchase_order.csv.
def new_inventory_adder():
    print("Adding new inventory.")

    # This adds new inventory from a purchase-order.csv file.
    purchase_order_array = pd.read_csv("Purchase_order.csv", sep=";")

    # This is searching for duplicate items and combining them into one line.
    # It first identifies duplicates, then adjusts the quantities, then deletes lines with a quantity of zero.
    # This avoids changing the size of the dataframe before it's been cycled through.
    for i in range(len(purchase_order_array) - 1):
        if purchase_order_array.loc[i, 'Product Name'] == purchase_order_array.loc[i + 1, 'Product Name'] and \
                purchase_order_array.loc[i, 'Group Name'] == purchase_order_array.loc[i + 1, 'Group Name'] and \
                purchase_order_array.loc[i, 'Condition'] == purchase_order_array.loc[i + 1, 'Condition']:
            # This is creating a weighted average of the item costs.
            this_quantity = int(purchase_order_array.loc[i, 'Quantity'])
            next_quantity = int(purchase_order_array.loc[i + 1, 'Quantity'])
            this_price = float(purchase_order_array.loc[i, 'Purchase Price'])
            next_price = float(purchase_order_array.loc[i + 1, 'Purchase Price'])

            purchase_order_array.at[i + 1, 'Purchase Price'] = (
                                                                           this_quantity * this_price + next_quantity * next_price) / (
                                                                       this_quantity + next_quantity)
            purchase_order_array.at[i + 1, 'Quantity'] = this_quantity + next_quantity
            purchase_order_array.at[i, 'Quantity'] = 0

    # This is dropping the zeroes, which is surprisingly hard to do becasue Pandas keeps the original index.
    drop_index = []
    for i in range(len(purchase_order_array) - 1):
        if purchase_order_array.loc[i, 'Quantity'] < 1:
            drop_index.append(i)
    purchase_order_array = purchase_order_array.drop(purchase_order_array.index[drop_index]).reset_index(drop=True)
    # This updates the CSV so the zeroed out lines are removed.
    purchase_order_array.to_csv('/Users/-------/Desktop/pythonProject/Purchase_order.csv',
                                mode='w', index=False, header=True, sep=";")
    purchase_order_array = pd.read_csv("Purchase_order.csv", sep=";")

    # This navigates to the inventory and starts updating.
    if len(purchase_order_array) > 0:
        driver.get(WEBSITE + PRICING_PAGE)
        page_reset('full_catalog')

    while len(purchase_order_array) > 0:
        time.sleep(randrange(20) / 10 + 2)
        name = purchase_order_array.loc[0, 'Product Name']
        itemGroup = purchase_order_array.loc[0, 'Group Name']
        condition = purchase_order_array.loc[0]['Condition']
        quantity = int(purchase_order_array.loc[0]['Quantity'])
        cost = float(purchase_order_array.loc[0]['Purchase Price'])

        # This selects the item Group from the dropdown menu
        Group_selector = Select(driver.find_element(By.ID, "GroupNameId"))
        Group_selector.select_by_visible_text(itemGroup)

        # This inputs the name of the item and submits the inquiry
        search = driver.find_element(By.ID, "Search")
        search.clear()
        search.send_keys(name + Keys.ENTER)
        print("Searching for item name: " + name + " from the Group " + itemGroup)
        print("Condition " + condition + ". Quantity: " + str(quantity) + ". Cost: $" + str(cost))
        time.sleep(randrange(20) / 10 + 2)

        listings = driver.find_elements(By.CLASS_NAME, "product-listing")
        listing_number = 1

        for line in listings:
            # First I need to find the condition
            meta_data = line.find_element(By.CLASS_NAME, "product-listing__meta")
            metas = meta_data.find_elements(By.TAG_NAME, "span")
            name_area = line.find_element(By.CLASS_NAME, "product-listing__name")
            line_item_name = name_area.find_element(By.TAG_NAME, "a").text

            # If the condition and the name is a match, we check the quantity.
            if condition == metas[4].text and name == line_item_name:
                bid = line.find_elements(By.TAG_NAME, "input")
                try:
                    pending_purchase = int(bid[len(bid) - 1].get_attribute("value"))
                except:
                    pending_purchase = 0
                print(
                    str(listing_number) + ". Condition and name matched. Pending purchases is " + str(pending_purchase))

                # If the quantity is >0, we update the quantity.
                if pending_purchase > 0:
                    bid[len(bid) - 1].clear()
                    bid[len(bid) - 1].send_keys(pending_purchase + quantity)
                    print("Quantity updated from " + str(pending_purchase) + " to " + str(quantity + pending_purchase))

                # If the pending quantity is 0, we set the price to the greater of the lowest listing or the the_website price,
                # and update the quantity.
                else:
                    bid[len(bid) - 1].clear()
                    bid[len(bid) - 1].send_keys(quantity)
                    try:  # Multiplying the lowest price plus shipping by 1.1.
                        lowest_box = line.find_element(By.CLASS_NAME, "product-listing__lowest-listing")
                        prices_L = lowest_box.find_elements(By.TAG_NAME, "span")
                        lowest_price = 1.1 * (float(prices_L[1].text) + float(prices_L[2].text))
                    except:
                        lowest_price = 0

                    try:
                        market_box = line.find_element(By.CLASS_NAME, "product-listing__market-price")
                        prices_M = market_box.find_elements(By.TAG_NAME, "span")
                        market_price = float(prices_M[1].text)
                    except:
                        market_price = 0

                    new_ask = round(max(lowest_price, market_price), 2)
                    if new_ask < 0.5:
                        new_ask = cost * 3
                    bid[len(bid) - 2].clear()
                    bid[len(bid) - 2].send_keys(new_ask)
                    print("Price set: " + str(new_ask))
            listing_number += 1

        # this will find the first element called 'pricing-actions'
        exits = driver.find_element(By.TAG_NAME, "pricing-actions")
        buttons = exits.find_elements(By.TAG_NAME, "input")
        # this will find the last input in pricing-actions, which is the close button
        buttons[len(buttons) - 1].send_keys(Keys.ENTER)
        time.sleep(randrange(20) / 10 + 2)
        # This removes the top line from the purcahse order csv.
        purchase_order_array = purchase_order_array.drop([0])
        to_csv = purchase_order_array.to_csv(
            '/Users/-------/Desktop/pythonProject/Purchase_order.csv',
            mode='w', index=False, header=True, sep=";")
        purchase_order_array = pd.read_csv("Purchase_order.csv", sep=";")


# This is everything that will be run in a day.
def daily_routine():
    # These try loops will be run first thing in the morning, only once per day.
    try:
        pricelist_updater("purchases")
    except Exception as e:
        print("The purchases prices could not be updated because:")
        print(e)
    try:
        pricelist_updater("inventory")
    except Exception as e:
        print("The inventory prices could not be updated because:")
        print(e)
    try:
        new_inventory_adder()
    except Exception as e:
        print("New inventory could not be added because:")
        print(e)
    print("Compleated update number: 1")

    # Anything inside the while loop will be run additional times per day.
    updates = 1
    while updates < 6:  # This is how many times it will run per day.
        decihours = 8  # This x10 +10  is how many minutes it will wait between runs.
        if len(pd.read_csv("purchases_names.csv", sep=";")) > 149:
            decihours = 0
        else:
            decihours -= int(round(len(pd.read_csv("purchases_names.csv", sep=";"))/20, 0))
        try:  # This adds new items that have been manually scraped.
            new_item_helper(min(150, len(pd.read_csv("purchases_names.csv", sep=";"))))
        except Exception as e:
            print("The new_item_helper function failed because:")
            print(e)
        while decihours > 0:
            print(str(decihours) + "0 minutes remaining...")
            time.sleep(60*10)  # This is 10 minutes (60 seconds * 10 minutes).
            decihours -= 1
        try:
            pricelist_updater("purchases")
        except Exception as e:
            print("The purchases prices could not be updated because:")
            print(e)
        try:
            pricelist_updater("inventory")
        except Exception as e:
            print("The inventory prices could not be updated because:")
            print(e)
        updates += 1
        print("Compleated update number: " + str(updates))
        now = dt.datetime.now()
        print(now.strftime("%Y-%m-%d %H:%M:%S"))

    try:  # This adds new items that have been manually scraped.
        new_item_helper(len(pd.read_csv("purchases_names.csv", sep=";")))
    except Exception as e:
        print("The new_item_helper function failed because:")
        print(e)
    try:  # This removes items more than two weeks old at the end of the day.
        purchases_bids_cleanup()
    except Exception as e:
        print("The purchases_bids_cleanup function failed because:")
        print(e)

    print("!!-- THE DAILY ROUTINE HAS FULLY COMPLETED --!!")
    now = dt.datetime.now()
    print(now.strftime("%Y-%m-%d %H:%M:%S"))


# This runs the daily routine once before relying on the schedule.
# Comment/un-comment if you want it to run right away.
daily_routine()

# This launches the code every morning at the specified military time.
schedule.every().day.at("08:30").do(daily_routine)
while 1:
    schedule.run_pending()
    time.sleep(50)
