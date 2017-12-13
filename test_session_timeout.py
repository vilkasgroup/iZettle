import os
import sys
import unittest
import logging
import time
from iZettle import Izettle

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


class TestIzettle(unittest.TestCase):
    """ This tests if the integration works if the session expires before we
    anticipate. This simply waits for the for the sessino to expire, so it wil
    take a looooooong time """
    def test_session(self):
        client = Izettle(
            client_id=os.environ['IZETTLE_CLIENT_ID'],
            client_secret=os.environ['IZETTLE_CLIENT_SECRET'],
            user=os.environ['IZETTLE_USER'],
            password=os.environ['IZETTLE_PASSWORD'],
        )

        # it actually expires after 7200
        time.sleep(8000)

        # lets see if it refreshes the session...
        self.assertIsNotNone(client.get_all_products())


if __name__ == '__main__':
    unittest.main()
