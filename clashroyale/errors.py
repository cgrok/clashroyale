'''
MIT License

Copyright (c) 2017 kyb3r

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

class NotResponding(Exception):
    def __init__(self):
        self.code = 504
        self.error = 'API request timed out, please be patient.'
        super().__init__(self.error)

class RequestError(Exception):
    '''Base class for request errors'''
    def __init__(self, resp, data):
        self.response = resp
        self.code = getattr(resp, 'status', getattr(resp, 'status_code'))
        self.method = resp.method
        self.reason = resp.reason
        self.error = data.get('error')
        if 'message' in data:
            self.error = data.get('message')
        self.fmt = '{0.reason} ({0.code}): {0.error}'.format(self)
        super().__init__(self.fmt)

class NotFoundError(RequestError):
    '''Raised if the player/clan is not found.'''
    pass

class ServerError(RequestError):
    '''Raised if the api service is having issues'''
    pass

class Unauthorized(RequestError):
    '''Raised if you passed an invalid token.'''
    pass