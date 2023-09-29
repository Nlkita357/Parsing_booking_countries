from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
import pandas as pd
from openpyxl import load_workbook
from datetime import datetime
import time
import os
import pandas as pd
import json

def create_webdriver():
    path_to_driver = os.path.abspath('./chromedriver.exe')
    options = webdriver.ChromeOptions()

    s = ChromeService(executable_path=path_to_driver)
    driver = webdriver.Chrome(service=s, options=options)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.maximize_window()
    return driver

def get_max_page(driver, url):
    driver.get(url)
    element = '//li[@class="b16a89683f"]'
    #get all pages
    all_pages = driver.find_elements("xpath", element)
    # get the maximum page (i.e. the penultimate page)
    max_page = int(all_pages[len(all_pages)-1].text)
    return max_page

def get_date():
    current_datetime = datetime.now()
    checkin = f"{current_datetime.year}-{current_datetime.month}-{current_datetime.day}"
    checkout = f"{current_datetime.year}-{current_datetime.month}-{current_datetime.day + 1}"
    return checkin, checkout

def get_data_for_last_hotels_in_json():
    try:
        file = open("last_data.json")
    except:
        file = open("last_data.json", "w", encoding="utf-8")
        dict_for_data = {"index_country": 0, "page": 0}
        file.write(json.dumps(dict_for_data))

    load_dict = json.load(file)
    last_country = load_dict["index_country"]
    last_page = load_dict["page"]
    return last_country, last_page

def save_data_for_last_hotels_in_json(index_country, page):
    file = open("last_data.json", "w", encoding="utf-8")
    dict_for_data = {"index_country": index_country, "page": page}
    file.write(json.dumps(dict_for_data))
    file.close()
    return

def save_data_in_csv(df, name, country, address, price):
    row_data = [name, country, address, price]

    df.loc[len(df)] = row_data # Add data to DataFrame
    df.to_excel("booking_hotels.xlsx", index=False)

def hotels_data_parsing(driver, list_saved_hotels, df, country):
    #get list of names
    element_name = '//div[@class="f6431b446c a23c043802"]'
    raw_names = driver.find_elements("xpath", element_name)

    #get the list of links
    element_link = '//a[@class="e13098a59f"]'
    raw_links = driver.find_elements("xpath", element_link)

    #get prices with currency at the end
    element_price = '//span[@class="f6431b446c fbd1d3018c e729ed5ab6"]'
    raw_prices = driver.find_elements("xpath", element_price)

    #get the text from the names elements
    names = []
    for raw_name in raw_names:
        name = raw_name.text
        names.append(name)

    # get text from link elements
    links = []
    for raw_link in raw_links:
        link = raw_link.get_attribute("href")
        links.append(link)

    #remove extra cmbols from prices
    prices = []
    for raw_price in raw_prices:
        raw_price = raw_price.text
        price = raw_price.replace(" ", "").replace("rub.", "")
        prices.append(price)

    data = []
    for index, link in enumerate(links):
        if names[index] not in list_saved_hotels:

            driver.get(link)

            element_address = '//p[@class="address address_clean"]/span[1]'
            address = driver.find_element("xpath", element_address).text

            #save data to excel
            save_data_in_csv(df, names[index], country, address, prices[index])

            #save the name to the list so that we don't have to add data that already exists
            list_saved_hotels.append(names[index])
            time.sleep(2)
    return list_saved_hotels

def get_names_hotels():
    try:
        table = pd.read_excel("booking_hotels.xlsx")
        names_hotels = table["Название"].tolist()
    except:
        file = open("booking_hotels.xlsx", "w", encoding="utf-8")
        file.close()
        names_hotels = []
    return names_hotels

def get_data_from_excel(df):
    try:
        table = pd.read_excel("booking_hotels.xlsx")

        names_hotels = table["Название"].tolist()
        countries_hotels = table["Страна"].tolist()
        addresses_hotels = table["Адрес"].tolist()
        prices_hotels = table["Цена"].tolist()

        for index in range(len(names_hotels)):
            df.loc[len(df)] = [names_hotels[index], countries_hotels[index], addresses_hotels[index], prices_hotels[index]]

    except:
        pass
    return df

#list of countries to spar
#limit - minimum hotel price
#currency - currency

def main_pars_hotels(countries, limit=0, currency="usd"):
    countries.append(None)

    driver = create_webdriver()

    #get the last country and page that was bypassed last time
    start_country, start_page = get_data_for_last_hotels_in_json()

    #get a list of hotel names so we don't have to save repeated data
    list_saved_hotels = get_names_hotels()

    # Create an empty DataFrame to save the data
    df = pd.DataFrame(columns=['Name', 'Country', 'Address', 'Price'])
    df = get_data_from_excel(df)

    #cut in countries[start_county:-1] is needed to start traversing from the last uncompleted country
    for country in countries[start_country:-1]:
        #get dates for checkout
        checkin, checkout = get_date()
        #create a url to go to the country's hotels
        url_for_country = f"https://www.booking.com/searchresults.ru.html? ss={country}&ssne={country}&ssne_untouched={country}&src_elem=sb&lang=en&dest_type=country&no_rooms=1&group_children=0&nflt=ht_id%3D204%3Bprice%3D{currency}- {limit}-max-10&hotel=true&efdco=1&checkin={checkin}&checkout={checkout}"
        print(url_for_country)
        time.sleep(1)

        #if the selected country has no pages, the maximum page will be 1
        try:
            #get max_quentity_page
            max_quentity_page = get_max_page(driver, url_for_country)
        except:
            max_quentity_page = 1

        #cycle to go through all pages
        offset = 25 * start_page
        for page in range(start_page, max_quentity_page):
            #the url needs offset +25
            url_for_country_and_offset = url_for_country + f"&offset={offset}"
            driver.get(url_for_country_and_offset)
            offset += 25

            #parsing hotels and saving to a table
            #parameters needed for saving
            list_saved_hotels = hotels_data_parsing(driver, list_saved_hotels, df, country)

            # save country and page number to go directly to hotels that have not been passed yet
            # save the country index to use slicing in for
            # save the last subsequent page so that we can start from it at the next startup
            save_data_for_last_hotels_in_json(start_country, page + 1)
            time.sleep(2)

        # save the next country and reset the page to zero
        start_country += 1
        save_data_for_last_hotels_in_json(start_country, 0)
        time.sleep(4)
    print("Complete!")

if __name__ == "__main__":
    countries = [] #enter countries
    main_pars_hotels(countries)