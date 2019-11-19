import requests
from bs4 import BeautifulSoup
import re
from geopy.geocoders import Nominatim


# location = {
# 'street_address'  : '8005 Navajo St',
# 'city'            : 'Philadelphia',
# 'zipcode'         : '19118'}


def RepFinder(street_address, city, zipcode):
    try:
        geolocator = Nominatim()
        place = geolocator.geocode(street_address + ' ' + city + ' ' + zipcode)

        try:
            lat = str(place.latitude)
            lon = str(place.longitude)

            url  = 'http://www.legis.state.pa.us/cfdocs/legis/home/findyourlegislator/?doSearch=yes&addr='
            url += street_address.replace(' ','+')
            url += '&city='
            url += city.replace(' ','+')
            url += '&zipCode='
            url += zipcode
            url += '&fullAddr='
            url += street_address.replace(' ','+')
            url += '%2C+'
            url += city.replace(' ','+')
            url += '%2C+PA%2C+'
            url += zipcode
            url += '&geoLat='
            url += lat
            url += '&geoLng='
            url += lon
            url += '&geoResponse=OK#address'

            # City Hall
            # req = 'http://www.legis.state.pa.us/cfdocs/legis/home/findyourlegislator/?doSearch=yes&addr=1401+John+F+Kennedy+Blvd&city=Philadelphia&zipCode=19107&fullAddr=1401+John+F+Kennedy+Blvd%2C+Philadelphia%2C+PA%2C+19107&geoLat=39.9541298&geoLng=-75.16439909999997&geoResponse=OK%2C+PARTIAL+MATCH#address'

            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            table = soup.find('table', {'class': 'ResultTable'})

            # Spin through the table rows
            # for r, row in enumerate(table.findAll('tr')):
            #     cells = row.findAll('td')
            #     for c, cell in enumerate(cells):
            #         print r, c, '--->', cell.text.strip()

            rep =        list(list(table.findAll('tr'))[0])[3].text.strip()
            house_dist = int(list(list(table.findAll('tr'))[0])[5].text.strip().split()[-1])

            sen =        list(list(table.findAll('tr'))[1])[3].text.strip()
            sen_dist =   int(list(list(table.findAll('tr'))[1])[5].text.strip().split()[-1])

            return {'rep_first_name'    : rep.split()[0].title(),
                    'rep_last_name'     : rep.split()[1].title(),
                    'house_dist'        : int(house_dist),
                    'sen_first_name'    : sen.split()[0].title(),
                    'sen_last_name'     : sen.split()[1].title(),
                    'sen_dist'          : int(sen_dist)}

        except AttributeError:
            return False

    except: # I can't firgure out how to use Geopy error exceptions so this will catch any error
        return False
