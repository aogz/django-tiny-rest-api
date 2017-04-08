import json

from django.utils.six import text_type

import config
from api.restframework.utils import response, successful

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name='dispatch')
class APITokenAuthenticationMixin(object):

    """
    Simple token based authentication.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:
        Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """

    token_model = None
    keyword = 'Token'

    def dispatch(self, request, *args, **kwargs):
        code, message = self.authenticate(request)

        if not successful(code):
            return response({'error': code, 'message': message, 'docs': config.DOCS_URL}, code)

        return super(APITokenAuthenticationMixin, self).dispatch(request, *args, **kwargs)

    def get_model(self):
        return self.token_model

    @staticmethod
    def get_authorization_header(request):
        """
        Return request's 'Authorization:' header, as a bytestring.
        Hide some test client ickyness where the header can be unicode.
        """
        auth = request.META.get('HTTP_AUTHORIZATION', b'')
        if isinstance(auth, text_type):
            auth = auth.encode('utf-8')
        return auth

    def authenticate(self, request):
        auth = self.get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return 401, 'Invalid token header. No credentials provided.'

        if len(auth) == 1:
            return 401, 'Invalid token header. No credentials provided.'
        elif len(auth) > 2:
            return 401, 'Invalid token header. Token string should not contain spaces.'

        try:
            token = auth[1].decode()
        except UnicodeError:
            return 401, 'Invalid token header. Token string should not contain invalid characters.'

        return self.authenticate_credentials(request, token)

    def authenticate_credentials(self, request, key):
        model = self.get_model()

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Save information about requests

        try:
            token = model.objects.select_related('account').get(token=key)
        except model.DoesNotExist:
            return 401, 'Provided token not found.'

        return 200, 'Token was successfully authenticated.'

    def authenticate_header(self, request):
        return self.keyword
