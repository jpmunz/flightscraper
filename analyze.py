import os
import csv

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
            arrival_date, return_date = f.split('_')

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

print "Scraped on %s" % scrape_date
print
for flight in get_cheapest(data, 10):
    print str_flight(flight)

print
print "Days ahead looked: %s" % settings.DATE_WINDOW_SIZE
print "Minimum trip days: %s" % settings.MIN_TRIP_DAYS
print "Maximum trip days: %s" % settings.MAX_TRIP_DAYS
