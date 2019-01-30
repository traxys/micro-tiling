n = 0

def app(environ, start_response):
    """Simplest possible application object"""
    global n
    data = 'Hello, World {}!\n'.format(n).encode('utf-8')
    n += 1
    status = '200 OK'
    response_headers = [
        ('Content-type', 'text/plain'),
        ('Content-Length', str(len(data)))
    ]
    start_response(status, response_headers)
    return iter([data])
