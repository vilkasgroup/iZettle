iZettle python module
=====================

.. image:: https://img.shields.io/pypi/v/iZettle.svg
   :target: https://pypi.python.org/pypi/iZettle

.. image:: https://img.shields.io/travis/vilkasgroup/iZettle.svg
   :target: https://travis-ci.org/vilkasgroup/iZettle

.. image:: https://coveralls.io/repos/github/vilkasgroup/iZettle/badge.svg?branch=master
   :target: https://coveralls.io/github/vilkasgroup/iZettle?branch=master

This module uses iZettle `HTTP
API <https://github.com/iZettle/api-documentation>`__ to integrate to
`iZettle <https://www.izettle.com/>`__

To use this module, you need parter id/pw and izettle account. Set these
to these system variables:

* IZETTLE\_CLIENT\_ID (partner id) 
* IZETTLE\_CLIENT\_SECRET (parter password)
* IZETTLE\_USER (izettle username/email. The same you use to login at https://my.izettle.com/)
* IZETTLE\_PASSWORD (izettle user password. The same you use to login at https://my.izettle.com/)

example usage
~~~~~~~~~~~~~

::

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
