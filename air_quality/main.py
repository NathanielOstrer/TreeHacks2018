# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START app]
from __future__ import absolute_import

# CODE TO FIX REQUEST INCOMPLETE BUG IN GAE

# in situations where "requests" is being included by other packages, you may not be able to provide your own library
# this code patches the existing classes with the fix from https://github.com/kennethreitz/requests/compare/master...agfor:master


from requests.models import Response

from requests.packages.urllib3.exceptions import (
    DecodeError, ReadTimeoutError, ProtocolError, HeaderParsingError)
from requests.exceptions import (
    ChunkedEncodingError, ContentDecodingError, ConnectionError, StreamConsumedError)
from requests.utils import (
    stream_decode_response_unicode, iter_slices)


DEFAULT_REDIRECT_LIMIT = 30
CONTENT_CHUNK_SIZE = 10 * 1024
ITER_CHUNK_SIZE = 512


def iter_content(self, chunk_size=1, decode_unicode=False):
    """Iterates over the response data.  When stream=True is set on the
    request, this avoids reading the content at once into memory for
    large responses.  The chunk size is the number of bytes it should
    read into memory.  This is not necessarily the length of each item
    returned as decoding can take place.

    chunk_size must be of type int or None. A value of None will
    function differently depending on the value of `stream`.
    stream=True will read data as it arrives in whatever size the
    chunks are received. If stream=False, data is returned as
    a single chunk.

    If decode_unicode is True, content will be decoded using the best
    available encoding based on the response.
    """

    def generate():
        # Special case for google app engine.
        if hasattr(self.raw, 'stream'):
            try:
                if isinstance(self.raw._original_response._method, int):
                    while True:
                        chunk = self.raw.read(chunk_size, decode_content=True)
                        if not chunk:
                            break
                        yield chunk
            except ProtocolError as e:
                raise ChunkedEncodingError(e)
            except DecodeError as e:
                raise ContentDecodingError(e)
            except ReadTimeoutError as e:
                raise ConnectionError(e)
        else:
            # Standard file-like object.
            while True:
                chunk = self.raw.read(chunk_size)
                if not chunk:
                    break
                yield chunk

        self._content_consumed = True

    if self._content_consumed and isinstance(self._content, bool):
        raise StreamConsumedError()
    elif chunk_size is not None and not isinstance(chunk_size, int):
        raise TypeError("chunk_size must be an int, it is instead a %s." % type(chunk_size))
    # simulate reading small chunks of the content
    reused_chunks = iter_slices(self._content, chunk_size)

    stream_chunks = generate()

    chunks = reused_chunks if self._content_consumed else stream_chunks

    if decode_unicode:
        chunks = stream_decode_response_unicode(chunks, self)

    return chunks


# replace library method with gae fix above
Response.iter_content = iter_content

from requests.packages.urllib3.util import response

def assert_header_parsing(headers):
    """
    Asserts whether all headers have been successfully parsed.
    Extracts encountered errors from the result of parsing headers.

    Only works on Python 3.

    :param headers: Headers to verify.
    :type headers: `httplib.HTTPMessage`.

    :raises urllib3.exceptions.HeaderParsingError:
        If parsing errors are found.
    """

    # This will fail silently if we pass in the wrong kind of parameter.
    # To make debugging easier add an explicit check.
    # if not isinstance(headers, httplib.HTTPMessage):
    #    raise TypeError('expected httplib.Message, got {0}.'.format(
    #        type(headers)))

    defects = getattr(headers, 'defects', None)
    get_payload = getattr(headers, 'get_payload', None)

    unparsed_data = None
    if get_payload:  # Platform-specific: Python 3.
        unparsed_data = get_payload()

    if defects or unparsed_data:
        raise HeaderParsingError(defects=defects, unparsed_data=unparsed_data)

response.assert_header_parsing = assert_header_parsing


import logging

# import Flask webapp api
from flask import Flask
from flask import request

# import datastore api
from google.cloud import datastore

# import google cloud exceptions library
import google.cloud.exceptions

# import search library
# useful for GeoPoints parsing
from google.appengine.api import search

# import appengine db
# for datastore
from google.appengine.ext import db

# import datetime library
from datetime import datetime

# import json library
import json



app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello World!'


class aqi(db.Model):
  carbonmonoxide = db.FloatProperty()
  co2 = db.FloatProperty()
  respiratoryirritants = db.FloatProperty()

  location = db.StringProperty()
  datetime = db.StringProperty()

# webhook for inserting air quality data
@app.route('/insert')
def insert_data():
	# instantiate a client for the datastore
	client = datastore.Client()

	# get the air quality data from the request

	# parse air quality data
	carbonmonoxide = float(request.args.get('carbonmonoxide'))
	co2 = float(request.args.get('co2'))
	respiratoryirritants = float(request.args.get('respiratoryirritants'))
	
	# parse location gepoint
	location_string = request.args.get('location')

	# parse datetime
	datetime_val = datetime.fromtimestamp(int(request.args.get('datetime')))


	with client.transaction():
	    incomplete_key = client.key('aqi')

	    task = datastore.Entity(key=incomplete_key)

	    task.update({
	        'carbonmonoxide': carbonmonoxide,
	        'co2': co2,
	        'respiratoryirritants': respiratoryirritants,
	        'location': location_string,
	        'datetime': request.args.get('datetime')
	    })

	    client.put(task)
	return 'success'

@app.route('/getalldata')
def get_data():
	# create a query for 'aqi' objects
	query = db.GqlQuery('SELECT *')

	# get all objects in query
	results = query.run(batch_size=1000)

	result_list = list(results)

	maps = [{'carbonmonoxide': res.carbonmonoxide, 'co2': res.co2, 'respiratoryirritants': res.respiratoryirritants, 'location': res.location, 'datetime':res.datetime} for res in result_list]

	# return the aqi entities as a list put into a json object
	return json.dumps(maps)

@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

if __name__ == '__main__':
	app.run()

# [END app]
