import requests
import logging
import json
import uuid
import time

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
    api methods provided by iZettle in https://github.com/iZettle/api-documentation.
    All method take payload data as defined in the API and they all return the JSON from
    the API as-is in dictionary form.

    example usage:
    >>> from iZettle import Izettle, RequestException
    >>> client = Izettle(
    ...     client_id=os.environ['IZETTLE_CLIENT_ID'],
    ...     client_secret=os.environ['IZETTLE_CLIENT_SECRET'],
    ...     user=os.environ['IZETTLE_USER'],
    ...     password=os.environ['IZETTLE_PASSWORD'],
    ... )
    >>> uuid1 = str(uuid.uuid1())
    >>> client.create_product({'name': 'new product', 'uuid': uuid1})
    {}
    >>> # name is mandatory, but uuid is not
    >>> client.get_product(uuid1)
    {'uuid': '1cc7fa84-dfb0-11e7-86aa-e4a7a083a65d','name': 'new product' ... }
    >>> client.delete_product(uuid1)
    """
    oauth_url = "https://oauth.izettle.net/token"  # note .net vs .com
    base_url = "https://{}.izettle.com/organizations/self/{}"

    def __init__(self, client_id="", client_secret="", user="", password=""):
        """ initialize Izettle object that has token and is ready to use. """
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__user = user
        self.__password = password
        self.__token = None
        self.__valid_until = 0

        # The session is valid for 7200 seconds. Tests may want to change it, so
        # I use it as a variable, but you shouldn't need to touch it in normal use.
        self.__seconds_the_session_is_valid = 7140
        self.auth()

    def _authenticate_request(f):
        """ Decorator that adds the auth token to the request header
        and refreshes the token if needed """
        def __authenticate_request(self, *args, **kwargs):
            if(self.__valid_until < time.time()):
                logger.info("session is no longer valid. re-auhtorize!")
                self.auth()

            headers = {
                "Authorization": "Bearer {}".format(self.__token),
                'Content-Type': 'application/json'
            }
            logger.info("request header {}".format(headers))
            response = f(self, *args, headers=headers, **kwargs)

            # TODO: if the API responses, that the session in no longer valid
            # refresh the token here, and re-do the request.
            return response
        return __authenticate_request

    def _response_handler(f):
        """ Decorator that handles responses (throw errors etc, decode json etc.) """
        def __response_handler(self, *args, **kwargs):
            request = f(self, *args, **kwargs)
            logger.info("response status code {}".format(request.status_code))
            logger.info("response text:{}".format(request.text))

            # TODO, raise RequestException here if needed
            # or make a new decorator...
            if(request.status_code == 200):
                return request.json()
            return {}
        return __response_handler

    @_response_handler
    @_authenticate_request
    def create_product(self, data={}, headers={}):
        """ create a new product (POST)
        exmpale with mandatory fields:
        >>> client = Izettle(...)  # See __init__
        >>> client.create_product({'name': 'name', 'vatPercentage': 0})
        See more: https://github.com/iZettle/api-documentation/blob/master/product-library.adoc
        """
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
        request = requests.post(url, data=json_data, headers=headers)
        return request

    @_response_handler
    @_authenticate_request
    def update_product(self, uuid, data={}, headers={}):
        """ update excisting product (PUT)
        example:
        >>> client.update_product(uuid, {'name': 'new name'})
        See more: https://github.com/iZettle/api-documentation/blob/master/product-library.adoc
        """

        # TODO, decorator should handle this, if UUID is provided
        headers['If-Match'] = '*'

        url = Izettle.base_url.format('products', 'products/v2/' + uuid)
        json_data = json.dumps(data)
        request = requests.put(url, data=json_data, headers=headers)
        return request

    @_response_handler
    @_authenticate_request
    def get_all_products(self, data={}, headers={}):
        """ get all products. Note: This does not take any parameters """
        url = Izettle.base_url.format('products', 'products')
        return requests.get(url, headers=headers)

    @_response_handler
    @_authenticate_request
    def get_product(self, uuid, data={}, headers={}):
        logger.info('\nUUID:')
        logger.info(uuid)
        url = Izettle.base_url.format('products', 'products/' + uuid)
        return requests.get(url, headers=headers)

    @_response_handler
    @_authenticate_request
    def delete_product(self, uuid, data={}, headers={}):
        url = Izettle.base_url.format('products', 'products/' + uuid)
        return requests.delete(url, headers=headers)

    def auth(self):
        """ Authenticate the session. Session is valid for 7200 seconds """
        data = {
            'grant_type': 'password',
            'username': self.__user,
            'password': self.__password,
            'client_id': self.__client_id,
            'client_secret': self.__client_secret,
        }
        request = requests.post(Izettle.oauth_url, data=data)

        if(request.status_code != 200):
            raise RequestException("Invalid response", request)

        response = request.json()
        self.__token = response['access_token']
        if(not self.__token):
            raise RequestException("Token missing", request)
        self.__valid_until = time.time() + self.__seconds_the_session_is_valid
