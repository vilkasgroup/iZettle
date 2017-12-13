# iZettle python module 

This module uses iZettle [HTTP API](https://github.com/iZettle/api-documentation) to integrate to [iZettle](https://www.izettle.com/)

To use this module, you need parter id/pw and izettle account. Set these to these system variables:
* IZETTLE_CLIENT_ID (partner id)
* IZETTLE_CLIENT_SECRET (parter password)
* IZETTLE_USER (izettle user name/email. The same you use to login at https://my.izettle.com/)
* IZETTLE_PASSWORD (izettle user password. The same you use to login at https://my.izettle.com/)

### example usage
```
import os
import uuid
from iZettle import Izettle, RequestException
client = Izettle(
    client_id=os.environ['IZETTLE_CLIENT_ID'],
    client_secret=os.environ['IZETTLE_CLIENT_SECRET'],
    user=os.environ['IZETTLE_USER'],
    password=os.environ['IZETTLE_PASSWORD'],
)
uuid1 = str(uuid.uuid1())
client.create_product({'name': 'new product', 'uuid': uuid1})
client.get_product(uuid1)
client.delete_product(uuid1)
```
