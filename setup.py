from distutils.core import setup

setup(name='private-domains',
        description='System for managing private domains. Includes server and client.',
        version='0.1',
        author='Szymon Sidor',
        author_email='szymon.sidor@gmail.com',
        url='https://github.com/nivwusquorum/private-domains'
        py_modules=['private_domains'],
        data_files=[('data', ['data/schema.sql', 'bm/b2.gif'])],
        scripts=['scripts/pd'],
        ]
)
