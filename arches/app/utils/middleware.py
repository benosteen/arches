import time
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.models import User, AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from django.utils.six import text_type
from django.utils.translation import ugettext as _
from arches.app.models.system_settings import settings
from arches.app.utils.response import Http401Response
from arches.app.utils.betterJSONSerializer import JSONSerializer, JSONDeserializer
from jose import jwt, jws, JWSError

HTTP_HEADER_ENCODING = 'iso-8859-1'

## PYCALLGRAPH ---------------------------------------------------------- ##
from pycallgraph import Config
from pycallgraph import PyCallGraph
from pycallgraph.globbing_filter import GlobbingFilter
from pycallgraph.output import GraphvizOutput
import os

class PyCallGraphMiddleware(MiddlewareMixin):

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if 'graph' in request.GET:
            config = Config()
            CALLGRAPH_DIR = settings.CALLGRAPH_DIR or os.path.join(settings.ROOT_DIR, "callgraphs")
            # you might want to remove the django exclusion from here to probe further
            # Note that there is a lot of abstraction and the callgraph for it is huge
            config.trace_filter = GlobbingFilter(exclude=['django.*', 'pycallgraph.*', 'PyCallGraph.*'])
            path_called = request.get_full_path().replace("/?", "_withparams_").replace("&","+").replace("/", "_")
            if not os.path.isdir(CALLGRAPH_DIR):
                os.mkdir(CALLGRAPH_DIR)
            graphviz = GraphvizOutput(output_file=os.path.join(CALLGRAPH_DIR, "{0}-{1}.png".format(path_called, time.time())))
            pycallgraph = PyCallGraph(output=graphviz, config=config)
            pycallgraph.start()

            self.pycallgraph = pycallgraph

    def process_response(self, request, response):
        if 'graph' in request.GET:
            self.pycallgraph.done()

        return response
## PYCALLGRAPH END------------------------------------------------------- ##

class SetAnonymousUser(MiddlewareMixin):
    def process_request(self, request):
        # for OAuth authentication to work, we can't automatically assign 
        # the anonymous user to the request, otherwise the anonymous user is 
        # used for all OAuth resourse requests
        if request.path != reverse('oauth2:authorize') and request.user.is_anonymous():
            try:
                request.user = User.objects.get(username='anonymous')
            except:
                pass


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    tries to setup the user on the request object based on the JSON web token passed in with the request

    """

    def get_user_from_token(self, token):
        decoded_json = jws.verify(token, settings.JWT_KEY, algorithms=[settings.JWT_ALGORITHM])
        decoded_dict = JSONDeserializer().deserialize(decoded_json)

        username = decoded_dict.get('username', None)
        expiration = decoded_dict.get('expiration', None)

        user = None
        try:
            user = User.objects.get(username=username)
            if not user.is_active:
                raise Exception()
        except:
            raise AuthenticationFailed(_('User inactive or deleted.\n\n'))

        if int(expiration) < int(time.time()):
            raise AuthenticationFailed(_('Token Expired.\n\n'))

        return user or AnonymousUser()

    def process_request(self, request):
        assert hasattr(request, 'token'), (
            "The JSON authentication middleware requires token middleware "
            "to be installed. Edit your MIDDLEWARE setting to insert "
            "'arches.app.utils.middleware.TokenMiddleware' before "
            "'arches.app.utils.middleware.JWTAuthenticationMiddleware'."
        )

        # if there is a session and the user isn't anonymous then don't modify request.user
        if request.user.is_anonymous() and request.token is not '':
            # try to get the user info from the token if it exists
            try:
                user = self.get_user_from_token(request.token)
                request.user = SimpleLazyObject(lambda: user)
            except AuthenticationFailed as err:
                response = Http401Response(err.message, www_auth_header='Bearer', content_type='text/plain')
                return response
            except JWSError as err:
                response = Http401Response(err.message, www_auth_header='Bearer', content_type='text/plain')
                return response


class TokenMiddleware(MiddlewareMixin):
    """
    puts the Bearer token found in the request header onto the request object
    
    pulled from http://www.django-rest-framework.org

    """

    def get_authorization_header(self, request):
        """
        Return request's 'Authorization:' header, as a bytestring.
        Hide some test client ickyness where the header can be unicode.
        """
        auth = request.META.get('HTTP_AUTHORIZATION', b'').replace('Bearer ', '')
        if isinstance(auth, text_type):
            # Work around django test client oddness
            auth = auth.encode(HTTP_HEADER_ENCODING)
        return auth

    def process_request(self, request):
        token = self.get_authorization_header(request)
        request.token = token


class AuthenticationFailed(Exception):
    pass
