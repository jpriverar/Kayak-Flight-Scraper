import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from scrapper import Flight_Scrapper
from logger import Logger

def get_all_flights(origin, destination, departure_dates, return_dates):
    all_flights = []

    for origin_city in origin:
        # Creating a new scrapper for each origin city to avoid getting human confirmations
        scrapper = Flight_Scrapper(logger)
        for destination_city in destination:
            for departure_date in departure_dates:
                for return_date in return_dates:
                    try:
                        flights, wrappers = scrapper.get_flights(origin_city, destination_city, departure_date, return_date, load_attemps=2, modes=['cheap'])
                        all_flights.append(flights)
                        scrapper.logger.log(f'Succesfully scraped for {origin_city}-{destination_city}, {departure_date}-{return_date}')
                    except Exception as e:
                        #scrapper.logger.log(e)
                        scrapper.logger.log(f'Something went wront, could not perform this scrape, trying the next one...')
        # Deleting the current scrapper to create a new one
        scrapper.quit()

    all_flights = pd.concat(all_flights, ignore_index=True) 
    return all_flights

def sort_by_price(flights):
    def extract_price(s):
            return int(s[1:].replace(',', ''))
        
    sorted_flights = flights.copy()
    sorted_flights['real_price'] = sorted_flights['Price'].apply(extract_price)
    sorted_flights.sort_values('real_price', ignore_index=True, inplace=True)
    sorted_flights.drop('real_price', axis=1, inplace=True)
    return sorted_flights

def send_flight_email(sender, receivers, header, data):
    # Formatting message to send
    msg = MIMEMultipart()
    msg['Subject'] = "Flight search results "
    msg['From'] = sender[0]

    html = """\
    <html>
    <head>{0}</head>
    <body>
        {1}
    </body>
    </html>
    """.format(header, data)

    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    # Starting email server and login
    server = smtplib.SMTP('smtp.outlook.com', 587)
    server.ehlo()
    server.starttls()
    server.login(sender[0] , sender[1])

    # Sending the actual mail
    server.sendmail(msg['From'], receivers, msg.as_string())

if __name__ == '__main__':
    # Creating a logger instance
    logger = Logger()

    # Defining desired cities and dates
    #flights, wrappers = scrapper.get_flights('GDL', 'MAD', '2022-12-08', '2023-01-26', load_attemps=2)
    origin_cities = ['MEX']
    destination_cities = ['MAD']
    departure_dates = ['2022-12-10']#, '2022-12-11', '2022-12-12', '2022-12-13']
    return_dates = ['2023-01-25']#, '2023-01-26', '2023-01-27', '2023-01-28']

    # Getting requested info
    flights = get_all_flights(origin_cities, destination_cities, departure_dates, return_dates)
    sorted_flights = sort_by_price(flights)
    #print(sorted_flights)

    # Sending email with info
    sender = ('USERNAME', 'PASSWORD')
    receivers = ['RECEIVER']
    header = 'This are the top 100 results for your last search!'
    data = sorted_flights.head(100).to_html()

    try:
        send_flight_email(sender, receivers, header, data)
        logger.log(f'Flight search result email sent!')
    except:
        logger.log(f'Something went wrong, could not sent information email')
