#!/bin/bash
if  [ $(hostname) == "web417.webfaction.com" ]; then 
    WEBFUCKTION="true"
    WEBFUCKTION_PIP="--allow-external PIL --allow-insecure PIL"
    #WEBFUCKTION_VENVARGS="-p /home/agaiszymon/bin/python"
else
    WEBFUCKTION="false"
fi

diff .env/env_requirements.txt env_requirements.txt  >/dev/null 2>&1 || {
    echo "Environment changed. Updating environment."
    virtualenv-2.7 $WEBFUCKTION_VENVARGS --no-site-packages --distribute .env
    source .env/bin/activate
    pip install -r env_requirements.txt $WEBFUCKTION_PIP
    if [ $WEBFUCKTION == "true" ]; then
        echo "Installing custom version of PIL for webfaction..."
        pip uninstall PIL <<< $'y\n'
        pushd ~/src/PIL-1.1.7-webfaction
        python setup.py install
        popd
    fi
    cp env_requirements.txt .env/env_requirements.txt
}
. .env/bin/activate
