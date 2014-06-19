from datetime import datetime

from BeautifulSoup import BeautifulSoup
import requests
from models import Listing
from settings import MISS_THRESHOLD, INITIAL_MLS, ZIPS, MAX_PRICE, CITY1, CITY2


NO_LISTING = 'No listings found. '
LIST_PRICE = 'List Price'
ADDRESS = 'Address'
CITY = 'City'
COUNTY = 'County'
SUB_DIV = 'Proj/Subdiv'
LIST_DATE = 'List Date'


class ListingNotFound(Exception):
    """ An exception representing a missing listing. """
    pass


def scrape_listing(mls_id):
    url = 'http://www.utahrealestate.com/report/display/report/clientfull/type/1/listno/%s/' % mls_id

    # time.sleep(1) # let's give their server a break
    r = requests.get(url)
    soup = BeautifulSoup(r.text)

    if soup.find(text=NO_LISTING):
        print 'No listing text in mls id %s' % mls_id
        raise ListingNotFound

    table = soup.find('table', 'prop-overview-full')
    rows = table.findAll('tr')

    for row in rows:
        tds = row.findAll('td')
        label = tds[0].text.replace(':&nbsp;', '')
        value = tds[1].text

        if LIST_PRICE == label:
            list_price = value.replace('$', '').replace(',', '')
        if ADDRESS == label:
            address = value
        if CITY == label:
            city = value
            zip = city[-5:]
        if COUNTY == label:
            county = value
        if SUB_DIV == label:
            sub_div = value

        if len(tds) > 2:
            label = tds[2].text.replace(':&nbsp;', '')
            value = tds[3].text
            if LIST_DATE == label:
                list_date = value
                list_date = datetime.strptime(list_date, '%m/%d/%Y')

    last_scraped = datetime.now()

    return Listing(url=url, price=list_price,
                   zip_code=zip, mls=mls_id,
                   address=address, city=city,
                   county=county, sub_div=sub_div,
                   list_date=list_date, last_scraped=last_scraped)


def run_scraper(mls=INITIAL_MLS):
    misses = 0
    while (MISS_THRESHOLD > misses):
        try:
            existing_listing = Listing.get_listing(mls)
            listing = scrape_listing(mls)

            print 'Fetching Listing ID %s' % mls
            print 'Have existing listing? %s ' % (existing_listing is not None)

            if existing_listing:
                existing_listing.is_new = False
                if int(existing_listing.price) != listing.price:
                    existing_listing.price = listing.price
                    existing_listing.is_updated = True
                else:
                    existing_listing.is_updated = False
                existing_listing.save()
            else:
                if fits_criteria(listing):
                    print 'HIT'
                    listing.is_new = True
                    listing.save()
                else:
                    print 'MISS. Count: %s' % misses
            mls = mls + 1
            misses = 0
        except ListingNotFound:
            existing_listing = Listing.get_listing(mls)
            mls = mls + 1
            misses = misses + 1
            if existing_listing:
                existing_listing.active = False
                existing_listing.last_scraped = datetime.now()
                existing_listing.save()
            else:
                print 'misses are %s ' % misses


def fits_criteria(listing):
    print '%s zip in ZIPS %s?' % (listing.zip_code,
                                  listing.zip_code in ZIPS)

    match_zip = listing.zip_code in ZIPS
    match_price = int(listing.price) <= MAX_PRICE
    match_city = (listing.city.lower().startswith(CITY1)
                  or listing.city.lower().startswith(CITY2))

    return match_zip and match_price and match_city


