import os
import urllib
import logging

from presence_analyzer import main
from presence_analyzer.script import make_debug, make_app

logger = logging.getLogger(__name__)


def _save_to_file(data):
    """
    Saves data to file specified in config as USERS_XML_FILE.
    """
    with open(main.app.config['USERS_XML_FILE'], 'w') as f:
        f.write(data)


def _prepare_file():
    """
    Checks whether USERS_XML_FILE exists. If yes, it gets deleted before download is performed.
    """
    if os.path.isfile(main.app.config['USERS_XML_FILE']):
        logger.info('Found existing data file. Removing.')
        os.remove(main.app.config['USERS_XML_FILE'])


def _run_main():
    response = urllib.urlopen(main.app.config['USERS_XML_URL']).read()
    _prepare_file()
    _save_to_file(response)


def run():
    """
    Entry point for production file download.
    """
    main.app = make_app()
    _run_main()


def run_debug():
    """
    Behaves as run(), but uses debug app instance.
    """
    main.app = make_debug()

    # make_debug() returns a DebuggedApplication object with app being its variable. This hack is
    # used to make one name to be used in entire scope.
    main.app = main.app.app
    _run_main()
