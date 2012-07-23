import os
import csv
import requests
import json
import argparse
import calendar

from datetime import datetime
import settings

DATE_PRINT_FORMAT = "%a %b %d"

def read_results(results_directory):
    results = os.listdir(results_directory)

    if not results:
        print "No results found in directory %s" % settings.RESULT_DIR

    if settings.DEBUG:
        print "Looking at results in %s" % results_directory

    flights = []

    earliest_arrival_date = datetime.max
    latest_arrival_date = datetime.min

    smallest_trip = float('inf')
    largest_trip = float('-inf')

    for folder in results:

        airports, scrape_date = folder.split('_')
        leaving_from, going_to = airports.split('-')

        path = results_directory + '/' + folder

        for f in os.listdir(path):
            arrival_date, return_date = f.rstrip('.csv').split('_')

            reader = csv.reader(open(path + '/' + f, 'rb'))

            # Skip header row
            try:
                reader.next()
            except StopIteration:
                # Skip if file is empty
                continue

            scrape_datetime = datetime.strptime(scrape_date, settings.DATE_FOLDER_FORMAT)

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
                flight_info['trip_length'] = (return_datetime - arrival_datetime).days
                flight_info['duration'] = duration
                flight_info['days_in_advance'] = (arrival_datetime - scrape_datetime).days

                flights.append(flight_info)

    meta_data = {
        'from': leaving_from,
        'to': going_to,
        'window_size': (latest_arrival_date - earliest_arrival_date).days,
        'min_trip': smallest_trip,
        'max_trip': largest_trip,
    }

    return flights, meta_data

def reformat(date_string, old_format=settings.DATE_FILE_FORMAT, new_format=DATE_PRINT_FORMAT):
    return datetime.strptime(date_string, old_format).strftime(new_format)

def str_flight(flight):

    airlines = flight['allAirlines'].split('/')
    numbers = flight['allFlightNumbers'].split('/')

    flight_numbers = ",".join([line + '/' + number for line,number in zip(airlines, numbers)])

    info = "$%s %s -- %s    (%s), Stops #%s, Duration %s (days)" % \
            (flight['totalFare'], reformat(flight['arrival_date']), reformat(flight['return_date']), flight_numbers, flight['numberOfStops'], flight['duration'])

    return info

def get_cheapest(data, n):
    data.sort(key=lambda flight: float(flight['totalFare']))

    results = []

    results.append("")
    results.append("Cheapest " + str(n) + " flights")
    results.extend([str_flight(flight) for flight in data[:n]])

    return results

def get_average(data, key_func, label_func, header):

    averages = {}

    for flight in data:
        avg = averages.setdefault(key_func(flight), {'sum': 0, 'count': 0})

        avg['sum'] += float(flight['totalFare'])
        avg['count'] += 1

    results = []

    results.append("")
    results.append(header)

    computed = []

    for k in sorted(averages.keys()):
        average = (averages[k]['sum'] / averages[k]['count']) if averages[k]['count'] > 0 else 0
        average = round(average, 2)
        computed.append((label_func(k), average))

    computed.sort(key=lambda average: average[1])

    results.extend([label + ": " + str(average) for label, average in computed])

    return results


def get_average_per_days_in_advance(data):
    key_func = lambda flight: flight['days_in_advance']
    label_func = lambda k: str(k) + " Days"

    return get_average(data, key_func, label_func, "Average flight cost for days booked in advance")

def get_average_per_day(data):
    key_func = lambda flight: datetime.strptime(flight['arrival_date'], settings.DATE_FILE_FORMAT).weekday()
    label_func = lambda k: calendar.day_name[k]

    return get_average(data, key_func, label_func, "Average flight cost by day of the week")

def get_average_per_trip_length(data):
    key_func = lambda flight: flight['trip_length']
    label_func = lambda k: str(k) + " Days"

    return get_average(data, key_func, label_func, "Average flight cost per trip length")


def analyze(result_directory=None, upload=False, compute_cheapest=0, compute_average_per_day=False, compute_average_per_trip_length=False, compute_average_per_days_in_advance=False):
    data, meta_data = read_results(result_directory)

    result = []

    result.append("Leaving from %s going to %s" % (meta_data['from'], meta_data['to']))
    result.append("Size of date range: %s (days)" % meta_data['window_size'])
    result.append("Minimum trip length: %s (days)" % meta_data['min_trip'])
    result.append("Maximum trip length: %s (days)" % meta_data['max_trip'])

    if compute_cheapest:
        result.extend(get_cheapest(data, compute_cheapest))

    if compute_average_per_day:
        result.extend(get_average_per_day(data))

    if compute_average_per_trip_length:
        result.extend(get_average_per_trip_length(data))

    if compute_average_per_days_in_advance:
        result.extend(get_average_per_days_in_advance(data))

    if upload:
        upload_url = settings.DEBUG_UPLOAD_URL if settings.DEBUG else settings.UPLOAD_URL
        requests.post(upload_url, data={'content': json.dumps(result)})

    print "\n".join(result)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Analyze previously scraped flight information')

    parser.add_argument('--results-dir', default=settings.RESULT_DIR, help="Results directory to analyze, defaults to the most current")
    parser.add_argument('--upload', action='store_true', default=False,  help="Uploads results to a URL specified in localsettings")
    parser.add_argument('--cheapest', type=int, default=0, help="Computes the N cheapest overall flights")
    parser.add_argument('--average-per-day', action='store_true', default=False, help="Computes average flight cost per day of the week")
    parser.add_argument('--average-per-trip-length', action='store_true', default=False, help="Computes average flight cost per trip length")
    parser.add_argument('--average-per-days-in-advance', action='store_true', default=False, help="Computes average flight cost based on how far in advance the flight is booked")
    args = parser.parse_args()

    analyze(result_directory=args.results_dir, upload=args.upload, compute_cheapest=args.cheapest, compute_average_per_day=args.average_per_day, compute_average_per_trip_length=args.average_per_trip_length, compute_average_per_days_in_advance=args.average_per_days_in_advance)
