from time import time

import models
from scraper import run_scraper


if __name__ == '__main__':
    t0 = time()
    models.init_db()
    run_scraper()
    t1 = time()
    models.export_csv()
    models.export_json()
    print 'Completed in.  %f' % (t1 - t0)