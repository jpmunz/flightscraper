DEBUG=False

RESULT_DIR='results'

DATE_FORMAT = '%m/%d/%Y'
DATE_FILE_FORMAT = '%m-%d-%Y'
CSV_FIELDS = 'numberOfStops', 'totalFare', 'arrivalTime', 'departureTime', 'allAirlines', 'allFlightNumbers'


SEARCH_URL="http://travel.travelocity.com/flights/FlightsItineraryService.do"

ANYTIME="1200" # Special value used by Travelocity to indicate no time preference

FLIGHT_TYPE="roundtrip"
DATE_TYPE="EXACT_DATES"

LEAVING_TIME=ANYTIME
RETURNING_TIME=ANYTIME

TICKET_TYPE="ECONOMY"
FARE_TYPE="all"

NUM_ADULTS=1

FROM='sfo'
TO='yyz'


DATE_WINDOW_SIZE=9
MIN_TRIP_DAYS=7
MAX_TRIP_DAYS=14

# Overwrite these in localsettings if you wish to upload the results
DEBUG_UPLOAD_URL=None
UPLOAD_URL=None

try:
    from localsettings import *
except:
    pass
