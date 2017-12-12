import os
import sys
import unittest
import logging
import uuid
import time
from iZettle import Izettle, RequestException

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


class TestIzettle(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        """ Initialize iZettle client. Requires the following environment
        variables IZETTLE_CLIENT_ID, IZETTLE_CLIENT_SECRET, IZETTLE_USER,
        IZETTLE_PASSWORD. """
        super(TestIzettle, self).__init__(*args, **kwargs)
        self.client = Izettle(
            client_id=os.environ['IZETTLE_CLIENT_ID'],
            client_secret=os.environ['IZETTLE_CLIENT_SECRET'],
            user=os.environ['IZETTLE_USER'],
            password=os.environ['IZETTLE_PASSWORD'],
        )

    def test_instance(self):
        """ Test that the client was initialized correctly.
        If this fails, make sure that you have environment variables set
        for the TestIzettle.__init__ method """
        self.assertIsNotNone(self.client)
        self.assertIsNotNone(self.client._Izettle__client_id)
        self.assertIsNotNone(self.client._Izettle__client_secret)
        self.assertIsNotNone(self.client._Izettle__user)
        self.assertIsNotNone(self.client._Izettle__password)

    def test_auth(self):
        """ Test that we got token from izettle API """
        self.assertIsNotNone(self.client._Izettle__token)

    def test_invalid_client_id(self):
        """ Test client creation with invalid parameters """
        with self.assertRaises(RequestException) as re:
            Izettle(client_id='invalid')
        exception = re.exception
        self.assertEqual(exception.msg, "Invalid response")
        self.assertEqual(exception.request.status_code, 400)

    def test_product(self):
        uuid1 = str(uuid.uuid1())
        self.assertIsNotNone(self.client.create_product({
            'name': 'product1',
            'uuid': uuid1,
        }))

        # after product is sent to iZettle, it's not immediately usable
        #time.sleep(1)

        # TODO, name and uuid with get method

        self.assertIsNotNone(self.client.update_product(uuid1, {
            'name': 'updated product name',
        }))

        # TODO, name and uuid with get method


if __name__ == '__main__':
    unittest.main()
