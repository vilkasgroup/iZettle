import os
import sys
import unittest
import logging
import uuid
import time
from iZettle.iZettle import Izettle, RequestException

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
        self.assertEqual(exception.developer_message, "Invalid client_id")
        self.assertEqual(exception.request.json()['error'], "invalid_client")
        self.assertEqual(exception.request.status_code, 400)

    def test_discounts(self):
        c = self.client
        discount_uuid = str(uuid.uuid1())
        discount_percentage = '10'

        c.create_discount({
            'uuid': discount_uuid,
            'percentage': discount_percentage,
        })

        self.assertGreater(len(c.get_all_discounts()), 0)

        discount = c.get_discount(discount_uuid)
        self.assertEqual(discount['uuid'], discount_uuid)
        self.assertEqual(discount['percentage'], discount_percentage)

        new_name = 'new name'
        c.update_discount(discount_uuid, {'name': new_name})
        self.assertEqual(c.get_discount(discount_uuid)['name'], new_name)

        c.delete_discount(discount_uuid)
        with self.assertRaises(RequestException) as re:
            c.get_discount(discount_uuid)
        exception = re.exception
        self.assertEqual(exception.request.status_code, 404)

    def test_categories(self):
        c = self.client

        category_uuid = str(uuid.uuid1())
        category_name = 'category name'

        c.create_category({
            'uuid': category_uuid,
            'name': category_name
        })

        self.assertGreater(len(c.get_all_categroies()), 0)
        category = c.get_category(category_uuid)
        self.assertEqual(category['uuid'], category_uuid)

        # FUN FUN FUN. All categories have name converted to upper case...
        self.assertEqual(category['name'], category_name.upper())

        # Tough luck, categories do not have delete method.
        # Your account is now full of unwanted categories...

    def test_product(self):
        c = self.client

        uuid1 = str(uuid.uuid1())
        name = 'product1'

        with self.assertRaises(RequestException) as e:
            c.get_product(uuid1)
        self.assertEqual(e.exception.request.status_code, 404)
        self.assertIn('not found', e.exception.developer_message)

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
        self.assertEqual(exception.msg, "request error 404")
        self.assertEqual(exception.request.status_code, 404)

        uuid2 = str(uuid.uuid1())
        self.assertNotEqual(uuid1, uuid2)
        current_product_amount = len(c.get_all_products())
        c.create_product({'name': '1', 'uuid': uuid1})
        c.create_product({'name': '2', 'uuid': uuid2})
        self.assertEqual(len(c.get_all_products()), current_product_amount + 2)
        c.delete_product_list({'uuid': [uuid1, uuid2]})
        self.assertEqual(len(c.get_all_products()), current_product_amount)

    def test_purchases(self):
        c = self.client

        with self.assertRaises(TypeError):
            # Parameters need to be in data dict
            c.get_multiple_purchases(limit=1)

        with self.assertRaises(TypeError):
            # missing mandatory argument
            c.get_purchase()

        with self.assertRaises(RequestException) as e:
            # This order of course cannot be in the server, because we made up the uuid
            c.get_purchase(str(uuid.uuid1()))
        self.assertEqual(e.exception.request.status_code, 404)
        self.assertIn('not found', e.exception.developer_message)

        multiple_purchases = c.get_multiple_purchases({'limit': 1})
        self.assertEqual(len(multiple_purchases['purchases']), 1)

        purchase_uuid = multiple_purchases['purchases'][0]['purchaseUUID']
        single_purchase = c.get_purchase(purchase_uuid)
        self.assertEqual(purchase_uuid, single_purchase['purchaseUUID'])

        purchase_uuid1 = multiple_purchases['purchases'][0]['purchaseUUID1']
        single_purchase = c.get_purchase(purchase_uuid1)
        self.assertEqual(purchase_uuid, single_purchase['purchaseUUID'])

    @unittest.skip('This will take over 2 hours.')
    def test_session(self):
        """ This tests if the integration works if the session expires before we
        anticipate. This simply waits for the for the sessino to expire, so it wil
        take a looooooong time """
        self.client.__session_valid_until = time.time() + 9000
        time.sleep(8000)
        self.assertIsNotNone(self.client.get_all_products())


if __name__ == '__main__':
    unittest.main(verbosity=2)
