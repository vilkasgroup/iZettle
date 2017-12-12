import requests
import logging
import json
import uuid

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
    oauth_url = "https://oauth.izettle.net/token"  # note .net vs .com
    base_url = "https://{}.izettle.com/organizations/self/{}"

    def __init__(self, client_id="", client_secret="", user="", password=""):
        """ initialize Izettle object that has token and is ready to use. """
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__user = user
        self.__password = password
        self.__token = None
        self.auth()

    def append_header(f):
        """ Decorator that adds the auth token to the request header """
        def _append_header(self, *args, **kwargs):
            # TODO refresh token if invalid. (keep time and check response)
            headers = {
                "Authorization": "Bearer {}".format(self.__token),
                'Content-Type': 'application/json'
            }
            logger.info("request header {}".format(headers))
            request = f(self, *args, headers=headers, **kwargs)
            logger.info("response status code {}".format(request.status_code))
            logger.info("response rext:{}".format(request.text))

            # TODO, raise RequestException here if needed
            # or make a new decorator...
            return request
        return _append_header

    @append_header
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

    @append_header
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

    @append_header
    def get_product(self, data={}, headers={}):
        pass

    @append_header
    def delete_product(self, uuid, data={}, headers={}):
        pass

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


if __name__ == '__main__':
    import os
    import sys
    logger.level = logging.DEBUG
    stream_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stream_handler)

    client = Izettle(
        client_id=os.environ['IZETTLE_CLIENT_ID'],
        client_secret=os.environ['IZETTLE_CLIENT_SECRET'],
        user=os.environ['IZETTLE_USER'],
        password=os.environ['IZETTLE_PASSWORD'],
    )
    logger.info('\npost product...\n')
    client.create_product({'name': 'name', 'vatPercentage': 0})
    # client.update_product(data={'uuid': '65d5a3aa-df85-11e7-a0c5-e4a7a083a65d'})  # our own uuid
    # client.update_product(data={'uuid': '9168a25d-5c0e-440d-aa56-a74148bd36cc'})  # uuid from api
    # client.update_product({'name': 'asdf'})
