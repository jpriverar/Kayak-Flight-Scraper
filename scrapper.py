import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from random import randint
from time import sleep

class Flight_Scrapper:
    def __init__(self, logger):
        # Creating a logger object to write progress
        self.logger = logger
        self.sleep_time_min = 10
        self.sleep_time_max = 21

        # Creating a web driver to browse the internet
        self.logger.log('Initiating Chrome driver instance')
        self.driver = webdriver.Chrome()
        self.current_url = ""

        # Parameters and info to do the flight search
        self.search_modes = {'best':'bestflight', 'cheap':'price', 'quick':'duration'}
        self.all_field_xpath = {'Wrappers':'//*[@class = "resultWrapper"]',
                                'Depart_Time':'//*[@class = "section times"]//*[@class = "time-pair"][1]',  #'//*[@class = "depart-time base-time"]',
                                'Arrival_Time':'//*[@class = "section times"]//*[@class = "time-pair"][2]',  #'//*[@class = "arrival-time base-time"]',
                                'Stops':'//*[@class = "section stops"]',
                                'Duration':'//*[@class = "section duration allow-multi-modal-icons"]/*[@class = "top"]',
                                'Cities':'//*[@class = "section duration allow-multi-modal-icons"]/*[@class = "bottom"]',
                                'Prices':'//*[@class="price option-text"]'}

        self.logger.log('Waiting to make sure driver starts properly, sleeping...')
        sleep(5)

    def quit(self):
        self.driver.quit()

    def load_more(self):
        self.logger.log('Attempting to load more results...')

        try:
            more_results_xpath = '//a[@class = "moreButton"]'
            self.driver.find_element(By.XPATH, more_results_xpath).click()

            self.logger.log('More results loaded, sleeping...')
            sleep(randint(self.sleep_time_min, self.sleep_time_max))
        except Exception as e:
            print(e)
            self.logger.log('Something went wrong, could not get more results...')

    def change_mode_with_button(self,mode):
        self.logger.log('Changing to ' + mode + ' mode.')

        try:
            mode_button_xpath = f'//a[@data-code = "{self.search_modes[mode]}"]'
            self.driver.find_elements(By.XPATH, mode_button_xpath)[0].click()

            self.logger.log(f'{mode} mode active, sleeping...')
            sleep(randint(self.sleep_time_min, self.sleep_time_max))
        except Exception as e:
            print(e)
            self.logger.log('Something went wrong, could not change mode manually...')

    # Possible modes: cheap, best, quick
    def start_kayak(self, origin, destination, start_dates, end_dates, mode):
        # Check if user wants to check a mode in particular
        add_mode = ''
        if mode is not None:
            add_mode = '?sort={self.search_modes[mode]}_a'

        kayak = (f"https://www.kayak.com/flights/{origin}-{destination}/{start_dates}/{end_dates}{add_mode}")
        self.logger.log('Trying to get ' + kayak)

        try:
            # Getting the website
            self.driver.get(kayak)

            self.logger.log('Successfully accessed kayak, sleeping...')
            sleep(randint(self.sleep_time_min, self.sleep_time_max))
        except:
            self.logger.log(f'Something went wrong, could not get {kayak}...')

    def get_raw_data(self, xpath):
        results = self.driver.find_elements(By.XPATH, xpath)
        return [result.text for result in results]

    def get_data(self, xpath):
        results_raw = self.driver.find_elements(By.XPATH, xpath)
        results_text = [" ".join(result.text.split('\n')) for result in results_raw if result.text != '']
        return results_text

    def get_stops_from_wrappers(self, wrappers):
        departure_stops = ['' for _ in range(len(wrappers))]
        departure_n_stops = ['' for _ in range(len(wrappers))]
        return_stops = [0 for _ in range(len(wrappers))]
        return_n_stops = [0 for _ in range(len(wrappers))]

        base_index = 2

        for i, wrapper in enumerate(wrappers):
            departure_n_stops[i] = wrapper.split('\n')[base_index]
            if departure_n_stops[i] != 'nonstop': departure_stops[i] = wrapper.split('\n')[base_index+1]
            else: base_index -= 1

            return_n_stops[i] = wrapper.split('\n')[base_index+8]
            if return_n_stops[i] != 'nonstop': return_stops[i] = wrapper.split('\n')[base_index+9]
        
        return departure_n_stops, departure_stops, return_n_stops, return_stops

    def get_data_from_all_fields(self):
        departure_data = {}
        return_data = {}
        prices = []
        wrappers = []
        
        self.logger.log(f'Getting info from fields: {list(self.all_field_xpath)}')
        for key, val in self.all_field_xpath.items():
            # We dont actually want to process the wrapper so will call the raw method
            if key == 'Wrappers':
                wrappers = self.driver.find_elements(By.XPATH, self.all_field_xpath['Wrappers'])
                wrappers = [x.text for x in wrappers]
                continue

            try:
                results = self.get_data(val)
            except Exception as e:
                self.logger.log('Could not get this data, moving on')
            
            # Price is the only field that's only one per result
            if key == 'Prices':
                prices = results
                continue
            
            departure_data[key] = results[::2]
            return_data[key] = results[1::2]
            
        return wrappers, departure_data, return_data, prices

    def _display_dic(self, dic):
        for key, val in dic.items():
            print(f'{len(val)}, {key}')

    def generate_flights_df(self, wrappers, departure_data, return_data, prices):
        self.logger.log('Creating data frames from fetched info')
        self.logger.log(f'Info found: {len(wrappers)} elements')

        # Creating both data frames for departure and return and putting them together
        try:
            departure_df = pd.DataFrame.from_dict(departure_data)
            return_df = pd.DataFrame.from_dict(return_data)
            full_df = pd.concat([departure_df, return_df], axis=1)
            self.logger.log('Successfully created dataframe...')
        except:
             # Display dictionary lenghts
            print(len(wrappers), len(prices))
            print('departure')
            self._display_dic(departure_data)
            print('return')
            self._display_dic(return_data)
            self.logger.log('Dictionary dimensions are incorrect, trying to fix from raw wrapper data...')

            try:
                departure_n_stops, _, return_n_stops, _ = self.get_stops_from_wrappers(wrappers)
                departure_data['Stops'] = departure_n_stops
                return_data['Stops'] = return_n_stops

                departure_df = pd.DataFrame.from_dict(departure_data)
                return_df = pd.DataFrame.from_dict(return_data)
                full_df = pd.concat([departure_df, return_df], axis=1)
                self.logger.log('Successfully created dataframe...')

            except Exception as e:
                print(e)
                print('departure')
                self._display_dic(departure_data)
                print('return')
                self._display_dic(return_data)
        
        # Adding the multilavel column to the data frame
        column_array = [['Departure', 'Return'], departure_df.columns]
        column_index = pd.MultiIndex.from_product(column_array)
        full_df.columns = column_index
        
        # Adding the price column
        full_df['Price'] = prices
        
        return full_df
    
    def get_flights(self, origin, destination, departure_date, return_date, load_attemps=1, modes=['best', 'cheap', 'quick']):
        self.logger.log(f'STARTING getting flights from {origin} to {destination}, from {departure_date} to {return_date}')

        dfs = []
        full_wrappers = []

        # Getting results for passed modes
        for mode in modes:
            self.logger.log(f'TRYING info scrape for {mode} mode')
            # Getting the webpage
            self.start_kayak(origin, destination, departure_date, return_date, None)

            # Clicking the current mode button
            self.change_mode_with_button(mode)

            # Loading more results +15 results per load approx.
            for _ in range(load_attemps):
                self.load_more() 

            # Getting results 
            wrappers, departure_data, return_data, prices = self.get_data_from_all_fields()
            # Adding date to the dictionary
            departure_data['Date'] = [departure_date for _ in range(len(wrappers))]
            return_data['Date'] = [return_date for _ in range(len(wrappers))]

            # Generating the dictionary
            dfs.append(self.generate_flights_df(wrappers, departure_data, return_data, prices))
            full_wrappers += wrappers

        # Concatenating all dataframes into one
        full_df = pd.concat(dfs, ignore_index=True)
        return full_df, wrappers