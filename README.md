private-domains
===============

A small-server that allows you to have private password protected domains.


Install package:

        sudo python setup.py install

and run server:

        pd runserver <port>

to see available commands simply type

        pd


Disclaimer
===============

This is a very early version and probably has some bugs. Even though I took good care to ensure this application is secure, I cannot guarantee it. In particular since a secret is used to access the service you should run it over https.

Warning: this app is not optimized for large scale use. It's just for an individuals personal convenience.
If somebody wants to rewrite it with tornado, better database and in general take it forward, you are welcome to. Let me know I might even help :-)
