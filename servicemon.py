'''
Microservice monitoring base class

For Flask API see: http://flask.pocoo.org/docs/0.11/api

'''


import json
from datetime import datetime

import flask
import threading

from monitor_excepts import AlreadyRegistered, CannotUnregister, NoSuchEndpoint


#TODO: Add logging
###


###
# Utility classes and functions
###
class Singleton(type):
    '''
    Class used to support singletons.
    '''
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


###
# The monitor class
###
class ServiceMonitor(object):
    '''
    Add monitoring API endpoints to a child class.
    '''
    #__metaclass__ = Singleton
    _commands = {}
    _flaskapp = None

    def __init__(self, port=None, service_name=None, endpoints=None):
        '''
        Initialize the service monitoring class: register default endpoints
        and start up the flask listening thread.
        '''
        self._default_endpoints = {'state': ('service state', self._command_state),
                                   'showall': ('show registered commands', self._command_show_all),
                                   'help': ('show registered commands', self._command_show_all),
                                  }

        super(ServiceMonitor, self).__init__()
        self._service_name = service_name or self.service_name

        try:
            self._flask_port = port or self.monitor_port
        except AttributeError:
            self._flask_port = None

        self.register_multiple_endpoints(self._default_endpoints)
        self.register_multiple_endpoints(endpoints or {})
        if hasattr(self, 'statistics'):
            self.register_endpoint('status', 'statistics report', self._report_statistics)

        self._start_time = datetime.now().isoformat()

        # See: http://flask.pocoo.org/docs/0.11/api/#url-route-registrations
        self._flaskapp = flask.Flask(__name__)
        self._flaskapp.add_url_rule('/<monitor_request>', view_func=self._service_request)
        self._flask_thread = threading.Thread(target=self._flask_run_thread,
                                              args=(),
                                              kwargs={})
        self._flask_thread.start()

    def _flask_run_thread(self, *args, **kwargs):
        '''
        Run the flask thread.
        '''
        self._flaskapp.run(port=self._flask_port)
        return

    def _report_statistics(self, *args, **kwargs):
        '''
        We expect most services to make runtime statistics available, and so a
        convience endpoint is provided.  All the service need do is to define
        and maintain a 'statistics' dictionary.

        If the service creator wishes to implement their own service for this
        endpoint either don't have a 'statistics' variable or unregister this
        one.
        '''
        return self.report_dictionary(self.statistics)


    # # #
    # The following functions may be called by children to maintain
    # their endpoints.
    def register_multiple_endpoints(self, endpoints):
        '''
        Register several endpoints.
        '''
        for (epoint, args) in endpoints.items():
            self.register_endpoint(epoint, args[0], args[1])


    def register_endpoint(self, endpoint, description, handler):
        '''
        Register a (new) monitoring endpoint.
        '''
        if endpoint in self._commands.keys():
            raise AlreadyRegistered(endpoint)

        self._commands[endpoint] = (description, handler)


    def unregister_endpoint(self, endpoint):
        '''
        Unregister a monitoring endpoint.
        '''
        if endpoint not in self._commands.keys():
            raise NoSuchEndpoint(endpoint)

        if endpoint in self._default_endpoints.keys():
            raise CannotUnregister(endpoint)

        self._commands.pop(endpoint)


    def report_dictionary(self, dict_in):
        dict_json = self.do_dump(dict_in)
        for key in dict_in.keys():
            dict_in[key] = 0
        return dict_json


    def do_dump(self, payload):
        '''
        Support all commands by dumping the relevant JSON.
        '''
        return json.dumps([self._service_name,
                           {'current_time': datetime.now().isoformat()}, payload])


    # # #
    # The following commands are used by this base class and are
    # not to be called by inheriting (child) classes.
    def _command_state(self, **kwargs):     #pylint: disable=unused-argument
        '''
        Default/builtin command: service state.
        '''
        return self.do_dump({'status': 'up', 'start_time': self._start_time})


    def _command_show_all(self, **kwargs):  #pylint: disable=unused-argument
        '''
        Default/builtin command: show all registered commands.
        '''
        #self.do_dump({epoint:val[0] for epoint,val in self._commands.items()})
        showlist = {}
        for epoint, val in self._commands.items():
            showlist[epoint] = val[0]
        return self.do_dump(showlist)


    def _unknown_request(self, endpoint=None):
        return self.do_dump({endpoint: 'No such endpoint'})


    def _service_request(self, monitor_request):
        descr, epoint_entry = self._commands.get(monitor_request, ('', self._unknown_request))
        return epoint_entry(endpoint=monitor_request)


if __name__ == "__main__":
    service_mon = ServiceMonitor(service_name=__name__)
