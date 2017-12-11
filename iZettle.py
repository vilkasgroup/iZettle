import requests

url = "https://oauth.izettle.net/token"
clientId = "e67a0e24-44fa-40fe-adc4-3cb699506538"
clientSecret = "IZSECfad3216c-1f49-42eb-8d68-611981011236"


class izettle:
    def auth(self, user, pw):
        global url
        global clientId
        global clientSecret

        data = {
            'grant_type': 'password',
            'client_id': clientId,
            'client_secret': clientSecret,
            'username': user,
            'password': pw
        }
        r = requests.post(url, data=data)

        if(r.status_code != 200):
            raise Exception("request_error", r)

        json_response = r.json()
        self.__token = json_response['access_token']
        print(self.__token)


if __name__ == '__main__':
    client = izettle()
    client.auth("tatu.wikman@gmail.com", "")
