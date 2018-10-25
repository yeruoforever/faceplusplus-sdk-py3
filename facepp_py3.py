import requests
import requests_toolbelt
import sys
import socket
import urllib.request
import json
import os.path
import time

DEBUG_LEVEL = 1


class File(object):
    """an object representing a local file"""
    path = None

    def __init__(self, path):
        self.path = path

    def get_content(self):
        """read image content"""

        if os.path.getsize(self.path) > 2 * 1024 * 1024:
            raise APIError(-1, None, 'image file size too large')
        return open(self.path, 'rb')

    def get_filename(self):
        return os.path.basename(self.path)


class APIError(Exception):
    code = None
    """HTTP status code"""

    url = None
    """request URL"""

    body = None
    """server response body; or detailed error information"""

    def __init__(self, code, url, body):
        self.code = code
        self.url = url
        self.body = body

    def __str__(self):
        return 'code={s.code}\nurl={s.url}\n{s.body}'.format(s=self)

    __repr__ = __str__


class API(object):
    key = None
    secret = None
    server = 'https://api-cn.faceplusplus.com/facepp/v3/'
    decode_result = True
    timeout = None
    max_retries = None
    retry_delay = None

    def __init__(self, key, secret, srv=None,
                 decode_result=True, timeout=30, max_retries=10,
                 retry_delay=5):
        """
        :param srv: The API server address
        :param decode_result: whether to json_decode the result
        :param timeout: HTTP request timeout in seconds
        :param max_retries: maximal number of retries after catching URL error
            or socket error
        :param retry_delay: time to sleep before retrying"""
        self.key = key
        self.secret = secret
        if srv:
            self.server = srv
        self.decode_result = decode_result
        assert timeout >= 0 or timeout is None
        assert max_retries >= 0
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        _setup_apiobj(self, self, [])

    def update_request(self, request):
        """overwrite this function to update the request before sending it to
        server"""
        pass


def _setup_apiobj(self, api, path):
    if self is not api:
        self._api = api
        self._urlbase = api.server + '/'.join(path)

    lvl = len(path)
    done = set()
    for i in _APIS:
        if len(i) <= lvl:
            continue
        cur = i[lvl]
        if i[:lvl] == path and cur not in done:
            done.add(cur)
            setattr(self, cur, _APIProxy(api, i[:lvl + 1]))


class _APIProxy(object):
    _api = None
    """underlying :class:`API` object"""
    _urlbase = None

    def __init__(self, api, path):
        _setup_apiobj(self, api, path)

    def __call__(self, *args, **kargs):
        if len(args):
            raise TypeError('Only keyword arguments are allowed')
        headers = dict()
        fields = dict()
        fields['api_key'] = self._api.key
        fields['api_secret'] = self._api.secret
        for (k, v) in kargs.items():
            if isinstance(v, File):
                fields[k] = (v.get_filename(), v.get_content(), 'multipart/form-data')
            else:
                fields[k] = str(v)
        multipart = requests_toolbelt.MultipartEncoder(
            fields=fields
        )
        headers['Content-Type'] = multipart.content_type
        retry = self._api.max_retries
        while True:
            retry -= 1
            try:
                ret = requests.post(self._urlbase, data=multipart, timeout=self._api.timeout, headers=headers).content
                break
            except urllib.error.HTTPError as e:
                raise APIError(e.code, self._urlbase, e.read())
            except (socket.error, urllib.error.URLError) as e:
                if retry < 0:
                    raise e
                _print_debug('caught error: {}; retrying'.format(e))
                time.sleep(self._api.retry_delay)

        if self._api.decode_result:
            try:
                ret = json.loads(ret.decode("utf-8"))
            except Exception as e:
                raise APIError(-1, self._urlbase, 'json decode error, value={0!r}'.format(ret))
        return ret


def _print_debug(msg):
    if DEBUG_LEVEL:
        sys.stderr.write(str(msg) + '\n')


_APIS = [
    '/detect',
    '/compare',
    '/search',
    '/faceset/create',
    '/faceset/addface',
    '/faceset/removeface',
    '/faceset/update',
    '/faceset/getdetail',
    '/faceset/delete',
    '/faceset/getfacesets',
    '/face/analyze',
    '/face/getdetail',
    '/face/setuserid'
]

_APIS = [i.split('/')[1:] for i in _APIS]
