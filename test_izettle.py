import os
import sys
import unittest
import logging
import uuid
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
        c = self.client

        uuid1 = str(uuid.uuid1())
        name = 'product1'

        c.create_product({
            'name': name,
            'uuid': uuid1,
        })

        product = c.get_product(uuid1)
        self.assertEqual(product['uuid'], uuid1)
        self.assertEqual(product['name'], name)

        updated_name = 'updated product name'
        c.update_product(uuid1, {
            'name': updated_name,
        })

        updated_product = c.get_product(uuid1)
        self.assertEqual(updated_product['name'], updated_name)

        variant_uuid = str(uuid.uuid1())
        variant_name = 'variant name 1'
        c.create_product_variant(uuid1, {'uuid': variant_uuid})
        c.update_product_variant(uuid1, variant_uuid, {'name': variant_name})

        product_with_updated_variant = c.get_product(uuid1)
        found_the_new_variant = False
        for variant in product_with_updated_variant['variants']:
            if(variant['uuid'] != variant_uuid):
                continue
            self.assertEqual(variant['name'], variant_name)
            found_the_new_variant = True
        self.assertTrue(found_the_new_variant)

        c.delete_product_variant(uuid1, variant_uuid)
        variant_is_no_longer_in_product = True
        for variant in c.get_product(uuid1)['variants']:
            if(variant['uuid'] == variant_uuid):
                variant_is_no_longer_in_product = False
        self.assertTrue(variant_is_no_longer_in_product)

        c.delete_product(uuid1)
        with self.assertRaises(RequestException) as re:
            c.get_product(uuid1)
        exception = re.exception
        self.assertEqual(exception.msg, "error 404")
        self.assertEqual(exception.request.status_code, 404)

        uuid2 = str(uuid.uuid1())
        self.assertNotEqual(uuid1, uuid2)
        current_product_amount = len(c.get_all_products())
        c.create_product({'name': '1', 'uuid': uuid1})
        c.create_product({'name': '2', 'uuid': uuid2})
        self.assertEqual(len(c.get_all_products()), current_product_amount + 2)
        c.delete_product_list({'uuid': [uuid1, uuid2]})
        self.assertEqual(len(c.get_all_products()), current_product_amount)


if __name__ == '__main__':
    unittest.main()
