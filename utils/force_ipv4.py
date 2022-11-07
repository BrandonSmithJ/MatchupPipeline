import socket

class force_ipv4:
    """Monkey patch to force IPv4.

    Some sites seem not to respond consistently to 
    IPv6 requests; this context manager forces
    requests to be made using IPv4.

    """
    old_getaddrinfo = None 

    def __enter__(self):
        if socket.getaddrinfo.__name__ != 'new_getaddrinfo': 
            force_ipv4.old_getaddrinfo = socket.getaddrinfo

            def new_getaddrinfo(*args, **kwargs):
                responses = force_ipv4.old_getaddrinfo(*args, **kwargs)
                return [response
                        for response in responses
                        if response[0] == socket.AF_INET]
            new_getaddrinfo.__name__ = 'new_getaddrinfo'
            socket.getaddrinfo = new_getaddrinfo
        return self


    def __exit__(self, *args, **kwargs):
        if force_ipv4.old_getaddrinfo is not None:
            socket.getaddrinfo = force_ipv4.old_getaddrinfo


