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
        try:
            # This is most of the times the only error message that you'll get/need
            self.developer_message = request.json()['developerMessage']
        except(ValueError):
            # Could be, that the error wasn't returned by the iZettle server app, but rather
            # by the server, load balancer etc.
            logger.info('request error did not have json.')


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
    TODO: improve documentations and meka sure phinx can generate from them.
    """
    oauth_url = "https://oauth.izettle.net/token"
    product_url = "https://products.izettle.com/organizations/self/{}"
    purchase_url = "https://purchase.izettle.com/{}"
    image_url = "https://image.izettle.com/v2/images/organizations/self/products"
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

            logger.info("args {}".format(args))
            logger.info("kwargs {}".format(kwargs))
            response = f(self, *args, **kwargs)

            if(response.status_code == 401):
                logger.info(response.text)
                if(response.json()['errorType'] == 'ACCESS_TOKEN_EXPIRED'):
                    logger.info('session expired. re-authorize and try again!')
                    self.auth()
                    response = f(self, *args, **kwargs)

            return response
        return __authenticate_request

    def _response_handler(f):
        """ Decorator that handles responses (throw errors etc, decode json etc.) """
        @wraps(f)
        def __response_handler(self, *args, **kwargs):
            request = f(self, *args, **kwargs)
            logger.info("response status code: {}".format(request.status_code))
            logger.info("response text: {}".format(request.text))

            if(request.ok):
                if(request.text):
                    return request.json()
                return {}
            raise RequestException('error {}'.format(request.status_code), request)
        return __response_handler

    def _request(f):
        """ does a request.* call according the function name.
        get_* -> GET, create_* -> POST, update_* -> PUT, delete_* -> DELETE.
        The wrapped GET and DELETE methods need to return url (str).
        The wrapped POST and PUT methods need to return url and data used as content (tuple).

        example:
        >>> @_request
        >>> def post_foo():
        >>>     return 'www.example.com', {'foo': 'bar'}
        >>> @_request
        >>> def get_bar():
        >>>     return 'www.example.com' """
        @wraps(f)
        def __request(self, *args, **kwargs):
            headers = self.__headers
            timeout = Izettle.timeout

            request_parameters = {'headers': headers, 'timeout': timeout}
            additional_request_parameters = f(self, *args, **kwargs)
            if(type(additional_request_parameters) == tuple):
                url = additional_request_parameters[0]
                data = additional_request_parameters[1]
                json_data = json.dumps(data)
                request_parameters['data'] = json_data
            else:
                url = additional_request_parameters

            if(f.__name__.startswith('create_')):
                return requests.post(url, **request_parameters)

            if(f.__name__.startswith('update')):
                return requests.put(url, **request_parameters)

            if(f.__name__.startswith('get_')):
                return requests.get(url, **request_parameters)

            if(f.__name__.startswith('delete_')):
                return requests.delete(url, **request_parameters)
        return __request

    def compose3(f1, f2, f3):
        """ Use this to build decorator that combines 3 decorators.
        For example instead of this:

        >>> @foo
        >>> @bar
        >>> @foobear
        >>> def a: pass

        you can do this:

        >>> combined_decorator = compose(foo, bar, foobar)
        >>> @combined_decorator
        >>> def a: pass

        https://stackoverflow.com/questions/5409450 """
        return lambda x: f1(f2(f3(x)))
    combined_decorator = compose3(_response_handler, _authenticate_request, _request)

    @combined_decorator
    def create_product(self, data=None):
        """ create a new product (POST) """

        # TODO: change data={} from every method to data=None...
        if 'uuid' not in data:
            data['uuid'] = str(uuid.uuid1())

        if 'variants' not in data:
            data['variants'] = [{}]

        for variant in data['variants']:
            if 'uuid' not in variant:
                variant['uuid'] = str(uuid.uuid1())

        if 'vatPercentage' not in data:
            data['vatPercentage'] = '0'

        url = Izettle.product_url.format('products')
        return url, data

    @combined_decorator
    def update_product(self, uuid, data=None):
        """ update excisting product (PUT) """
        url = Izettle.product_url.format('products/v2/' + uuid)
        return url, data

    @combined_decorator
    def get_all_products(self):
        """ get all products. """
        return Izettle.product_url.format('products')

    @combined_decorator
    def get_product(self, uuid):
        """ get single product with uuid """
        return Izettle.product_url.format('products/' + uuid)

    @combined_decorator
    def delete_product(self, uuid):
        """ delete a single product """
        return Izettle.product_url.format('products/' + uuid)

    @_response_handler
    @_authenticate_request
    def delete_product_list(self, data=None):
        """ delete multiple products """
        url = Izettle.product_url.format('products')
        return requests.delete(url, params=data, headers=self.__headers, timeout=Izettle.timeout)

    @combined_decorator
    def create_product_variant(self, product_uuid, data=None):
        """ Create a product variant for a product """
        if 'uuid' not in data:
            data['uuid'] = str(uuid.uuid1())

        url = Izettle.product_url.format('products/{}/variants')
        url = url.format(product_uuid)
        return url, data

    @combined_decorator
    def update_product_variant(self, product_uuid, variant_uuid, data=None):
        """ update product variant """
        url = Izettle.product_url.format('products/{}/variants/{}')
        url = url.format(product_uuid, variant_uuid)
        return url, data

    @combined_decorator
    def delete_product_variant(self, product_uuid, variant_uuid):
        """ delete a variant of a product """
        url = Izettle.product_url.format('products/{}/variants/{}')
        return url.format(product_uuid, variant_uuid)

    @combined_decorator
    def get_all_categroies(self):
        """ get all categories. """
        return Izettle.product_url.format('categories')

    @combined_decorator
    def get_category(self, uuid):
        """ get single category with uuid """
        return Izettle.product_url.format('categories/' + uuid)

    @combined_decorator
    def create_category(self, data=None):
        """ create a new category """
        if 'uuid' not in data:
            data['uuid'] = str(uuid.uuid1())

        url = Izettle.product_url.format('categories')
        return url, data

    @combined_decorator
    def create_discount(self, data=None):
        """ create a new discount """
        if 'uuid' not in data:
            data['uuid'] = str(uuid.uuid1())

        url = Izettle.product_url.format('discounts')
        return url, data

    @combined_decorator
    def get_all_discounts(self):
        """ get all discounts. """
        return Izettle.product_url.format('discounts')

    @combined_decorator
    def get_discount(self, uuid):
        """ get single discount with uuid """
        return Izettle.product_url.format('discounts/' + uuid)

    @combined_decorator
    def delete_discount(self, uuid):
        """ delete a single discount """
        return Izettle.product_url.format('discounts/' + uuid)

    @combined_decorator
    def update_discount(self, uuid, data=None):
        """ update excisting discount """
        url = Izettle.product_url.format('discounts/' + uuid)
        return url, data

    @_response_handler
    @_authenticate_request
    def get_all_purchases(self, data=None):
        url = Izettle.purchase_url.format('purchases/v2')
        return requests.get(url, params=data, headers=self.__headers, timeout=Izettle.timeout)

    @combined_decorator
    def get_purchase(self, uuid):
        return Izettle.purchase_url.format('purchase/v2/' + uuid)

    @combined_decorator
    def create_image(self, data):
        return Izettle.image_url, data

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
        self.__headers = {
            "Authorization": "Bearer {}".format(self.__token),
            'Content-Type': 'application/json',
            'IF-Match': '*'  # TODO, use etag where needed
        }

        # TODO:
        # since every one is calling request methods with the same
        # "headers=self.__headers, timeout=Izettle.timeout", maybe
        # we should have some short hand for that...
        return request
