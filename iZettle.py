import requests
import logging

logger = logging.getLogger(__name__)


class RequestException(Exception):
    """ Exception raised when a request to iZettle API fails.
    This exception also incules the request object """
    def __init__(self, msg, request, *args, **kwargs):
        super(RequestException, self).__init__(*args, **kwargs)
        self.msg = msg
        self.request = request


class Izettle:
    url = "https://oauth.izettle.net/token"

    def __init__(self, client_id="", client_secret="", user="", password=""):
        """ initialize Izettle object that has token and is ready to use. """
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__user = user
        self.__password = password
        self.__token = None
        self.auth()

    def auth(self):
        """ Authenticate the session. Session is valid for 7200 seconds """
        data = {
            'grant_type': 'password',
            'username': self.__user,
            'password': self.__password
        }
        request = self._request(data)
        response = request.json()
        self.__token = response['access_token']
        if(not self.__token):
            raise RequestException("Token missing", request)

    def _request(self, data):
        """ Do a post request to iZettle API with client id and secret
        appended to the data. Raises RequestException """
        data['client_id'] = self.__client_id
        data['client_secret'] = self.__client_secret

        logger.info("do request with data {}".format(data))
        r = requests.post(Izettle.url, data=data)
        logger.info("got response {}".format(r.text))

        if(r.status_code != 200):
            raise RequestException("Invalid response", r)

        return r
