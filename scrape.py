import requests
import json
from datetime import datetime, timedelta
import csv
import os

import settings


def search(leave_date, return_date):
    query_params = {
        'flightType': settings.FLIGHT_TYPE,
        'dateTypeSelect': settings.DATE_TYPE,
        'leavingDate': leave_date,
        'leavingFrom': settings.FROM,
        'goingTo': settings.TO,
        'dateLeavingTime': settings.LEAVING_TIME,
        'dateReturningTime': settings.RETURNING_TIME,
        'returningDate': return_date,
        'adults': settings.NUM_ADULTS,
        'classOfService': settings.TICKET_TYPE,
        'fareType': settings.FARE_TYPE
    }

    response = requests.get(settings.SEARCH_URL, params=query_params)

    return json.loads(response.text)


def search_range(start_day, end_day, min_trip_length, max_trip_length):
    '''
    For everyday D from startday to (endday - MIN_LENGTH)
    get results for querying D to E in (D + MIN_LENGTH to min(endday, (D + MAX_LENGTH))
    '''

    # The results for each date range will be stored in a directory named by
    # the timestamp of the first day searched
    result_path = settings.RESULT_DIR + '/' + start_day.strftime(settings.DATE_FILE_FORMAT)

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

            writer = csv.writer(open(result_path + '/' + file_name, 'wb+'))

            # Header row
            writer.writerow(settings.CSV_FIELDS)

            try:
                result = search(leave_date.strftime(settings.DATE_FORMAT), \
                                return_date.strftime(settings.DATE_FORMAT))

                for flight in result['results']:
                    writer.writerow([flight[field] for field in settings.CSV_FIELDS])

            except Exception, e:
                print "Failed to perform search %s" % e.message


now = datetime.now()
search_range(now, now + timedelta(settings.DATE_WINDOW_SIZE), settings.MIN_TRIP_DAYS, settings.MAX_TRIP_DAYS)
