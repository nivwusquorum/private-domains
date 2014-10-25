from distutils.core import setup

setup(name='private-domains',
        description='System for managing private domains. Includes server and client.',
        version='0.1',
        author='Szymon Sidor',
        author_email='szymon.sidor@gmail.com',
        url='https://github.com/nivwusquorum/private-domains',
        packages=['private_domains'],
        package_data={'private_domains': ['templates/*.html', 'data/*.sql']},
        scripts=['pd'],
        install_requires=[
            'requests>=2.4.3',
            'flask>=0.10.1',
        ],
)
