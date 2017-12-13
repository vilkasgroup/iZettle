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
        name = 'product1'
        self.assertIsNotNone(self.client.create_product({
            'name': name,
            'uuid': uuid1,
        }))

        product = self.client.get_product(uuid1)
        self.assertEqual(product['uuid'], uuid1)
        self.assertEqual(product['name'], name)

        updated_name = 'updated product name'
        self.assertIsNotNone(self.client.update_product(uuid1, {
            'name': updated_name,
        }))

        updated_product = self.client.get_product(uuid1)
        self.assertEqual(updated_product['name'], updated_name)

        self.client.delete_product(uuid1)

        # now that the product is deleted, get_product should return empty set
        deleted_product = self.client.get_product(uuid1)
        self.assertFalse(deleted_product)

        uuid2 = str(uuid.uuid1())
        self.assertNotEqual(uuid1, uuid2)
        current_product_amount = len(self.client.get_all_products())
        self.client.create_product({'name': '1', 'uuid': uuid1})
        self.client.create_product({'name': '2', 'uuid': uuid2})
        self.assertEqual(len(self.client.get_all_products()), current_product_amount + 2)
        self.client.delete_product_list({'uuid': [uuid1, uuid2]})
        self.assertEqual(len(self.client.get_all_products()), current_product_amount)

    def test_expired_session(self):
        # Normaly the session is valid for 7200 seconds, but I want to
        # see that it still works if the client thinks that the session
        # has expired.
        #
        # TODO: assert if it actually refreshed the session
        # https://stackoverflow.com/questions/3829742/assert-that-a-method-was-called-in-a-python-unit-test
        #
        # TODO. Try also setting the session valid time to bigger than 7200
        # seconds, then wait for 7200 seconds to test if it can handle that
        # too (it should, but it hasn't been tested yet).
        Izettle.seconds_the_session_is_valid = 1
        self.client.auth()
        time.sleep(2)
        self.client.get_all_products()


if __name__ == '__main__':
    unittest.main()
