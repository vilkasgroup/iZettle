import requests
import logging
import json
import uuid
import time
from functools import wraps

logger = logging.getLogger(__name__)


class RequestException(Exception):
    """ Exception raised when a request to iZettle API fails (either by the API
    returning an error or we not getting what we were expecting for)
    This exception also incules the request object (with a possible response)"""
    def __init__(self, msg, request, *args, **kwargs):
        super(RequestException, self).__init__(*args, **kwargs)
        self.msg = msg
        self.request = request


class Izettle:
    """ This class handles session and has helper method for most of the
    api methods provided by iZettle API.
    All method pass the payload as-is and returns results as-is (with JSON
    encoding/decoding and some error handling by raising RequestException)

    example usage:
    >>> from iZettle import Izettle, RequestException
    >>> client = Izettle(
    ...     client_id=os.environ['IZETTLE_CLIENT_ID'],
    ...     client_secret=os.environ['IZETTLE_CLIENT_SECRET'],
    ...     user=os.environ['IZETTLE_USER'],
    ...     password=os.environ['IZETTLE_PASSWORD'],
    ... )
    >>> client.create_product({'name': 'new product'})
    """
    oauth_url = "https://oauth.izettle.net/token"
    base_url = "https://{}.izettle.com/organizations/self/{}"
    timeout = 30

    def __init__(self, client_id="", client_secret="", user="", password=""):
        """ Initialize Izettle objec and create sessions. """
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__user = user
        self.__password = password
        self.__token = None
        self.__refresh_token = None
        self.__session_valid_until = 0
        self.auth()

    def _authenticate_request(f):
        """ Decorator that adds the auth token to the request header
        and refreshes the token if needed """
        @wraps(f)
        def __authenticate_request(self, *args, **kwargs):
            if(self.__session_valid_until < time.time()):
                logger.info("session expired. re-auhtorize!")
                self.auth()

            headers = {
                "Authorization": "Bearer {}".format(self.__token),
                'Content-Type': 'application/json'
            }
            logger.info('call function {}'.format(f.__name__))
            response = f(self, *args, headers=headers, **kwargs)

            if(response.status_code == 401):
                if(response.json()['errorType'] == 'ACCESS_TOKEN_EXPIRED'):
                    logger.info('session expired. re-authorize and try again!')
                    self.auth()
                    response = f(self, *args, headers=headers, **kwargs)

            return response
        return __authenticate_request

    def _response_handler(f):
        """ Decorator that handles responses (throw errors etc, decode json etc.) """
        @wraps(f)
        def __response_handler(self, *args, **kwargs):
            request = f(self, *args, **kwargs)
            logger.info("response status code {}".format(request.status_code))
            logger.info("response text:{}".format(request.text))

            if(request.ok):
                if(request.text):
                    return request.json()
                return {}
            raise RequestException('error {}'.format(request.status_code), request)
        return __response_handler

    @_response_handler
    @_authenticate_request
    def create_product(self, data={}, headers={}):
        """ create a new product (POST) """
        if 'uuid' not in data:
            data['uuid'] = str(uuid.uuid1())

        if 'variants' not in data:
            data['variants'] = [{}]

        for variant in data['variants']:
            if 'uuid' not in variant:
                variant['uuid'] = str(uuid.uuid1())

        if 'vatPercentage' not in data:
            data['vatPercentage'] = '0'

        url = Izettle.base_url.format('products', 'products')
        json_data = json.dumps(data)
        return requests.post(url, data=json_data, headers=headers, timeout=Izettle.timeout)

    @_response_handler
    @_authenticate_request
    def update_product(self, uuid, data={}, headers={}):
        """ update excisting product (PUT) """
        headers['If-Match'] = '*'

        url = Izettle.base_url.format('products', 'products/v2/' + uuid)
        json_data = json.dumps(data)
        return requests.put(url, data=json_data, headers=headers, timeout=Izettle.timeout)

    @_response_handler
    @_authenticate_request
    def get_all_products(self, data={}, headers={}):
        """ get all products. Note: This does not take any parameters """
        url = Izettle.base_url.format('products', 'products')
        return requests.get(url, headers=headers, timeout=Izettle.timeout)

    @_response_handler
    @_authenticate_request
    def get_product(self, uuid, data={}, headers={}):
        """ get single product with uuid """
        url = Izettle.base_url.format('products', 'products/' + uuid)
        return requests.get(url, headers=headers, timeout=Izettle.timeout)

    @_response_handler
    @_authenticate_request
    def delete_product(self, uuid, data={}, headers={}):
        """ delete a single product """
        url = Izettle.base_url.format('products', 'products/' + uuid)
        return requests.delete(url, headers=headers, timeout=Izettle.timeout)

    @_response_handler
    @_authenticate_request
    def delete_product_list(self, data={}, headers={}):
        """ delete multiple products """
        url = Izettle.base_url.format('products', 'products')
        return requests.delete(url, params=data, headers=headers, timeout=Izettle.timeout)

    @_response_handler
    @_authenticate_request
    def create_product_variant(self, product_uuid, data={}, headers={}):
        """ Create a product variant for a product """
        if 'uuid' not in data:
            data['uuid'] = str(uuid.uuid1())

        url = Izettle.base_url.format('products', 'products/{}/variants')
        url = url.format(product_uuid)

        json_data = json.dumps(data)
        return requests.post(url, data=json_data, headers=headers, timeout=Izettle.timeout)

    @_response_handler
    @_authenticate_request
    def update_product_variant(self, product_uuid, variant_uuid, data={}, headers={}):
        """ update product variant """
        headers['If-Match'] = '*'

        url = Izettle.base_url.format('products', 'products/{}/variants/{}')
        url = url.format(product_uuid, variant_uuid)
        json_data = json.dumps(data)
        return requests.put(url, data=json_data, headers=headers, timeout=Izettle.timeout)

    @_response_handler
    @_authenticate_request
    def delete_product_variant(self, product_uuid, variant_uuid, headers={}):
        url = Izettle.base_url.format('products', 'products/{}/variants/{}')
        url = url.format(product_uuid, variant_uuid)

        return requests.delete(url, headers=headers, timeout=Izettle.timeout)

    @_response_handler
    def auth(self):
        """ Authenticate the session. Session is valid for 7200 seconds """
        if(self.__refresh_token):
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.__refresh_token
            }
        else:
            data = {
                'grant_type': 'password',
                'username': self.__user,
                'password': self.__password,
            }

        data['client_id'] = self.__client_id,
        data['client_secret'] = self.__client_secret,
        request = requests.post(Izettle.oauth_url, data=data, timeout=Izettle.timeout)

        if(request.status_code != 200):
            raise RequestException("Invalid response", request)

        logger.info('session authorized: {}'.format(request.text))
        response = request.json()
        self.__token = response['access_token']
        self.__refresh_token = response['refresh_token']
        self.__session_valid_until = time.time() + response['expires_in'] - 60
        return request
