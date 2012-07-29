import requests
import json
from datetime import datetime, timedelta
import csv
import os
import argparse

import settings


def search(leave_date, return_date, query_params):
    query_params.update({
        'leavingDate': leave_date,
        'returningDate': return_date,
    });

    if settings.DEBUG:
        query_string=[key + "=" + str(value) for key, value in query_params.iteritems()]
        print settings.SEARCH_URL + '?' + '&'.join(query_string)

    # Need to spoof the cookies so it doesn't reject the request
    # TODO this is pretty brittle, not sure when it will stop working
    cookies = {
        'JSESSIONID':	'BC3DC263DC6AF33B1E635B7CCC2A1029.p0600',
        'TUID':	'252a5b55-d831-49d8-803b-419bd22f430c',
    }

    response = requests.get(settings.SEARCH_URL, params=query_params, cookies=cookies)

    return json.loads(response.text)


def search_range(start_day, end_day, min_trip_length, max_trip_length, query_params):
    '''
    For everyday D from startday to (endday - MIN_LENGTH)
    get results for querying D to E in (D + MIN_LENGTH to min(endday, (D + MAX_LENGTH))
    '''

    # The results for each date range will be stored in a directory named by
    # the timestamp of the first day searched


    trip =  query_params['leavingFrom'] + '-' + query_params['goingTo']
    timestamp = datetime.now().strftime(settings.DATE_FOLDER_FORMAT)

    result_path = settings.RESULT_DIR + '/' + trip + '_' + timestamp


    if not os.path.exists(result_path):
        os.makedirs(result_path)

    min_trip_length = timedelta(min_trip_length)
    max_trip_length = timedelta(max_trip_length)

    for start in range(0, (end_day - min_trip_length - start_day).days + 1):

        leave_date = (start_day + timedelta(start))

        if settings.DEBUG:
            print "FROM: " + leave_date.strftime(settings.DATE_FORMAT)

        for end in range(min_trip_length.days, max_trip_length.days + 1):
            return_date = (leave_date + timedelta(end))

            if return_date > end_day:
                break;

            if settings.DEBUG:
                print "     TO: " + return_date.strftime(settings.DATE_FORMAT)

            # The results for each FROM to TO date range are written to 
            # a seperate file
            file_name = "%s_%s.csv" % (leave_date.strftime(settings.DATE_FILE_FORMAT), \
                                        return_date.strftime(settings.DATE_FILE_FORMAT))

            try:
                result = search(leave_date.strftime(settings.DATE_FORMAT), \
                                return_date.strftime(settings.DATE_FORMAT), \
                                query_params)

                if 'errors' in result:
                    if settings.DEBUG:
                        print "No results found"
                    continue

                writer = csv.writer(open(result_path + '/' + file_name, 'wb+'))

                # Header row
                writer.writerow(settings.CSV_FIELDS)

                for flight in result['results']:
                    writer.writerow([flight[field] for field in settings.CSV_FIELDS])

            except Exception, e:
                print "Failed to perform search %s" % e.message
                continue


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Scrape travelocity.com for flight information')

    parser.add_argument('departure', help='Airport code for departure')
    parser.add_argument('destination', help='Airport code for arrival')
    parser.add_argument('start_date', help='Earliest possible start date of the trip to check (MM/DD/YYYY)')
    parser.add_argument('end_date', help='Latest possible end date of the trip to check (MM/DD/YYYY)')

    parser.add_argument('--min-duration', type=int, default=settings.MIN_TRIP_DAYS, help="Shortest possible trip duration")
    parser.add_argument('--max-duration', type=int, default=settings.MAX_TRIP_DAYS, help="Longest possible trip duration")
    parser.add_argument('--num-adults', type=int, default=settings.NUM_ADULTS, help="Number of adults flying")

    parser.add_argument('--relative-dates', action='store_true', default=False, help="start and end date will be interpreted as number of days from present")

    args = parser.parse_args()

    if(args.relative_dates):
        now = datetime.now()
        start = now + timedelta(int(args.start_date))
        end = now + timedelta(int(args.end_date))
    else:
        start = datetime.strptime(args.start_date, settings.DATE_FORMAT)
        end = datetime.strptime(args.end_date, settings.DATE_FORMAT)

    # These are using camelCased keys to match the travelocity REST API
    query_params = {
        'goingTo': args.destination.lower(),
        'leavingFrom': args.departure.lower(),
        'adults': args.num_adults,
        'classOfService': settings.TICKET_TYPE,
        'fareType': settings.FARE_TYPE,
        'dateReturningTime': settings.RETURNING_TIME,
        'dateLeavingTime': settings.LEAVING_TIME,
        'dateTypeSelect': settings.DATE_TYPE,
        'flightType': settings.FLIGHT_TYPE,
    }

    search_range(start, end, args.min_duration, args.max_duration, query_params)
