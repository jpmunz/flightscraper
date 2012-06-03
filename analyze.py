import os
import csv
import requests
import json

from datetime import datetime
import settings


DATE_PRINT_FORMAT = "%a %b %d"

def read_latest_results():
    results = os.listdir(settings.RESULT_DIR)

    if results:
        results.sort(key=lambda f: datetime.strptime(f, settings.DATE_FILE_FORMAT))

        if settings.DEBUG:
            print "Looking at results in %s" % results[-1]

        result_path = settings.RESULT_DIR + '/' + results[-1]
        flights = []
        for f in os.listdir(result_path):
            arrival_date, return_date = f.rstrip('.csv').split('_')

            reader = csv.reader(open(result_path + '/' + f, 'rb'))

            # Skip header row
            reader.next()

            for row in reader:
                flight_info = dict(zip(settings.CSV_FIELDS, row))

                flight_info['arrival_date'] = arrival_date
                flight_info['return_date'] = return_date

                flights.append(flight_info)

        return flights, results[-1]


def get_cheapest(data, n):
    data.sort(key=lambda flight: float(flight['totalFare']))
    return data[:n]


def reformat(date_string, old_format=settings.DATE_FILE_FORMAT, new_format=DATE_PRINT_FORMAT):
    return datetime.strptime(date_string, old_format).strftime(new_format)

def str_flight(flight):

    airlines = flight['allAirlines'].split('/')
    numbers = flight['allFlightNumbers'].split('/')

    flight_numbers = ",".join([line + '/' + number for line,number in zip(airlines, numbers)])

    info = "$%s %s -- %s    (%s)" % \
            (flight['totalFare'], reformat(flight['arrival_date']), reformat(flight['return_date']), flight_numbers)

    return info

data, scrape_date = read_latest_results()

result = []

result.append("Scraped on %s" % scrape_date)
result.append("")
result.extend([str_flight(flight) for flight in get_cheapest(data, 10)])
result.append("")
result.append("Days ahead looked: %s" % settings.DATE_WINDOW_SIZE)
result.append("Minimum trip days: %s" % settings.MIN_TRIP_DAYS)
result.append("Maximum trip days: %s" % settings.MAX_TRIP_DAYS)


upload_url = None

if settings.DEBUG:
    upload_url = settings.DEBUG_UPLOAD_URL
elif hasattr(settings, 'UPLOAD_URL'):
    upload_url = settings.UPLOAD_URL

if upload_url:
    response = requests.post(upload_url, data={'content': json.dumps(result)})

print "\n".join(result)
