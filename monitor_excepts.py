'''
Microservice monitoring exceptions

'''


###
# Custom exceptions
###
class AlreadyRegistered(Exception):
    '''
    Exception raised attempting to register an endpoint already registered.
    '''
    def __init__(self, message):
        super(AlreadyRegistered, self).__init__('Endpoint {} is already registered'.format(message))

class NoSuchEndpoint(Exception):
    '''
    Exception raised attempting to de-register an unregistered endpoint.
    '''
    def __init__(self, message):
        super(NoSuchEndpoint, self).__init__('No such registered endpoint {}'.format(message))

class CannotUnregister(Exception):
    '''
    Some endpoints cannot be unregistered.
    '''
    def __init__(self, message):
        super(CannotUnregister, self).__init__('Cannot unregister endpoint {}'.format(message))
