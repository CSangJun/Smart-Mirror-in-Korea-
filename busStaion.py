from __future__ import unicode_literals
import grequests
try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote
import re
import xml.etree.ElementTree

try:
    from urllib.parse import urlunparse, urlparse, urlencode
except ImportError:
    from urlparse3 import urlparse, urlunparse
    from urllib import urlencode

try:
    import configparser as cp
except ImportError:
    import ConfigParser as cp

config = cp.RawConfigParser()

try: #python2
    config.read('config')
except UnicodeDecodeError:
    config.read('config',encoding='utf-8')

def ConfigSectionMap(section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def make_url(url, qs):
    url_parts = list(urlparse(url))
    url_parts[4] = urlencode(qs)
    u = urlunparse(url_parts)
    return u

def create_bus_qs(serviceKey, station_id):
    qs = dict()
    qs['serviceKey'] = unquote(serviceKey)
    qs['arsId'] = station_id
    return qs

arrival_api_url = 'http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid'
key = ConfigSectionMap("api_key")['bus']
station_id = ConfigSectionMap("bus")['station_id']


def bus_grequests(url, key, station_id):
    bus_qs = create_bus_qs(key, station_id)
    return grequests.get(make_url(url, bus_qs))


def bus_request():
    return bus_grequests(arrival_api_url, key, station_id)

route_id = ConfigSectionMap("bus")['route_id']


def parse_time_string(time_string):
    """
    parse time string into arrival object
    :param time_string: "12분33초후[2번째 전]"
    :return: list (minutes, seconds, stops)
    """
    pattern = re.compile('(?:(?P<min>\d+)분|)(?:(?P<sec>\d+)초|)후\[(?P<stops>\d+)번째 전\]')
    match = pattern.search(time_string)

    s = None

    if match is not None:
        m = match.group('min')
        s = match.group('sec')
        stops = match.group('stops')  # digit

        if m is None:  # "33초후[2번째 전]"
            m = 0
        if s is None:  # "12분후[10번째 전]
            s = 0

        s = (int(m), int(s), int(stops))
    return s


def convert_arrmsg(msg):
    """
    convert arrmsg into arrival object
    :param msg: arrmsg on XML response
    :return: list (minutes, seconds, stops)
    """

    arrival = None

    if msg == '곧 도착':
        arrival = (0, 0, 0)
    else:
        arrival = parse_time_string(msg)

    return arrival


def arrivals_from_xml(root):
    """
    get arrivals from xml which contains arrival items (n different routes) for specified bus station
    :param root: root node of xml response
    :return: arrival list (this, next)
    """

    arrivals = (None, None)

    try:
        # find matching route
        route_item = None
        for item in root[2]:
            if item.find('busRouteId').text == route_id:
                route_item = item
                break

        if route_item is not None:
            text1 = route_item.find('arrmsg1').text
            arrival1 = convert_arrmsg(route_item.find('arrmsg1').text)
            arrival2 = convert_arrmsg(route_item.find('arrmsg2').text)
            arrivals = (arrival1, arrival2)

    except xml.etree.ElementTree.ParseError as e:
        print("XML error", str(e))
        print(xml.etree.ElementTree.tostring(root))

    return arrivals


def arrival_to_str(arrival):
    """
    :param arrival: list (minutes, seconds, stops)
    :return: arrival string
             example : '4m(3)' for 4 minutes and 3 stops left
    """

    arrival_str = "----"

    if arrival is not None:
        # omit seconds
        arrival_str = '{}m({})'.format(arrival[0], arrival[2])

    return arrival_str


def bus_arrival_view(arrivals):
    """
    create bus arrival view from arrivals
    :param arrivals: (arrival, arrival, arrival...)
    :return: string "arrival_str/arrival_str/arrival_str..."
    """

    view = ""

    for index, element in enumerate(arrivals):
        if index != 0:
            view += '/'

        view += arrival_to_str(element)

    return view