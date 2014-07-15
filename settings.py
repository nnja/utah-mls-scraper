from models import Listing

MISS_THRESHOLD = 50
ZIPS = ['84121']
MAX_PRICE = 350000
CITY1 = 'cottonwood'
CITY2 = 'salt'

# INITIAL_MLS = 1239271, 1206693, 1204927
INITIAL_MLS = Listing.get_last_mls()
