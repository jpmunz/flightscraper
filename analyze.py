import os
import csv
import requests
import json
import argparse

from datetime import datetime
import settings

DATE_PRINT_FORMAT = "%a %b %d"

def read_results(results_directory):
    results = os.listdir(settings.RESULT_DIR)

    if not results:
        print "No results found in directory %s" % settings.RESULT_DIR

    if not results_directory:
        # Grab the latest based on timestamp
        # Directories are of the form: FROM-TO_TIMESTAMP
        results.sort(key=lambda f: datetime.strptime(f.split('_')[1], settings.DATE_FOLDER_FORMAT))

        results_directory = results[-1]

    if settings.DEBUG:
        print "Looking at results in %s" % results_directory

    result_path = settings.RESULT_DIR + '/' + results_directory
    flights = []

    earliest_arrival_date = datetime.max
    latest_arrival_date = datetime.min

    smallest_trip = float('inf')
    largest_trip = float('-inf')

    for f in os.listdir(result_path):
        arrival_date, return_date = f.rstrip('.csv').split('_')

        reader = csv.reader(open(result_path + '/' + f, 'rb'))

        # Skip header row
        reader.next()

        arrival_datetime = datetime.strptime(arrival_date, settings.DATE_FILE_FORMAT)
        return_datetime = datetime.strptime(return_date, settings.DATE_FILE_FORMAT)

        earliest_arrival_date = min(earliest_arrival_date, arrival_datetime)
        latest_arrival_date = max(latest_arrival_date, return_datetime)

        duration = (return_datetime - arrival_datetime).days

        smallest_trip = min(smallest_trip, duration)
        largest_trip = max(largest_trip, duration)

        for row in reader:
            flight_info = dict(zip(settings.CSV_FIELDS, row))

            flight_info['arrival_date'] = arrival_date
            flight_info['return_date'] = return_date
            flight_info['duration'] = duration

            flights.append(flight_info)

    airports, timestamp = results_directory.split('_')
    leaving_from, going_to = airports.split('-')

    meta_data = {
        'scrape_date': timestamp,
        'from': leaving_from,
        'to': going_to,
        'window_size': (latest_arrival_date - earliest_arrival_date).days,
        'min_trip': smallest_trip,
        'max_trip': largest_trip,
    }

    return flights, meta_data

def get_cheapest(data, n):
    data.sort(key=lambda flight: float(flight['totalFare']))
    return data[:n]


def reformat(date_string, old_format=settings.DATE_FILE_FORMAT, new_format=DATE_PRINT_FORMAT):
    return datetime.strptime(date_string, old_format).strftime(new_format)

def str_flight(flight):

    airlines = flight['allAirlines'].split('/')
    numbers = flight['allFlightNumbers'].split('/')

    flight_numbers = ",".join([line + '/' + number for line,number in zip(airlines, numbers)])

    info = "$%s %s -- %s    (%s), Stops #%s, Duration %s (days)" % \
            (flight['totalFare'], reformat(flight['arrival_date']), reformat(flight['return_date']), flight_numbers, flight['numberOfStops'], flight['duration'])

    return info


def analyze(num_results_to_show=None, result_directory=None, upload=False):
    data, meta_data = read_results(result_directory)

    result = []

    result.append("Leaving from %s going to %s" % (meta_data['from'], meta_data['to']))
    result.append("Scraped on %s" % meta_data['scrape_date'])
    result.append("")
    result.extend([str_flight(flight) for flight in get_cheapest(data, num_results_to_show)])
    result.append("")
    result.append("Size of date range: %s (days)" % meta_data['window_size'])
    result.append("Minimum trip length: %s (days)" % meta_data['min_trip'])
    result.append("Maximum trip length: %s (days)" % meta_data['max_trip'])

    if upload:
        upload_url = settings.DEBUG_UPLOAD_URL if settings.DEBUG else settings.UPLOAD_URL
        requests.post(upload_url, data={'content': json.dumps(result)})

    print "\n".join(result)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Analyze previously scraped flight information')

    parser.add_argument('--results-dir', help="Results directory to analyze, defaults to the most current")
    parser.add_argument('--show', type=int, default=10, help="Number of results to show")
    parser.add_argument('--upload', action='store_true', default=False,  help="Uploads results to a URL specified in localsettings")

    args = parser.parse_args()

    analyze(num_results_to_show=args.show, result_directory=args.results_dir, upload=args.upload)
