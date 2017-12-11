import requests


class RequestException(Exception):
    # TODO: evaluate, if we really need our own exception, or should we just
    # use Exception instead?
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
        """ get authentication token from izettle API.
        Raises RequestException """
        # TODO: Check if we have token already, and try to refresh that one
        data = {
            'grant_type': 'password',
            'client_id': self.__client_id,
            'client_secret': self.__client_secret,
            'username': self.__user,
            'password': self.__password
        }
        r = requests.post(Izettle.url, data=data)

        if(r.status_code != 200):
            raise RequestException("Invalid response", r)

        json_response = r.json()
        self.__token = json_response['access_token']

        if(not self.__token):
            raise RequestException("Token missing", r)
