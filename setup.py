from setuptools import setup, find_packages
from io import open

def read(filename):
    with open(filename, encoding='utf-8') as file:
        return file.read()


setup(name='roschatAsyncBotPythonSDK',
      version='0.0.1',
      packages=find_packages(),
      long_description=read('README.md'),
      long_description_content_type="text/markdown",
      author='g1es0n',
      url='https://github.com/g1es0n/roschat-async-bot-python-sdk',
      install_requires=['aiohttp', 'python-socketio[asyncio_client]>=5.8.0'],
      )