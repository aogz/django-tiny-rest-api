from django.http import Http404, HttpResponseServerError
from django.views.generic import View

from api.restframework.auth import APITokenAuthenticationMixin
from api.restframework.utils import response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail, get_connection
from django.conf import settings


@method_decorator(csrf_exempt, name='dispatch')
class APIView(APITokenAuthenticationMixin, View):
    model = None
    fields = []
    search_by = None
    order_by = None
    limit = 20
    search_options = {}
    allowed_fields = {}
    extra_fields = []

    def get_fields(self, request):
        fields = request.GET.get('fields')
        fields = fields.replace(' ', '').split(',') if fields else self.fields
        return fields

    def get(self, request, *args, **kwargs):
        if len(kwargs.keys()):
            return self.get_one(request, **kwargs)
        else:
            return self.get_list(request, *args, **kwargs)

    def get_object(self, key, filters=None):
        filter_parameter = self.search_by + '__iexact'
        filter_set = {filter_parameter: key}
        filter_set.update(filters or {})
        additional_values = []
        for av in self.allowed_fields.values():
            if type(av) is list:
                additional_values += av
            else:
                additional_values.append(av)

        values = self.fields + additional_values
        item = self.model.objects.filter(**filter_set).values(*values)
        if len(item) > 1:
            connection = get_connection(host=settings.GMAIL_HOST,
                                        port=settings.GMAIL_PORT,
                                        username=settings.GMAIL_HOST_USER,
                                        password=settings.GMAIL_HOST_PASSWORD,
                                        user_tls=settings.GMAIL_USE_TLS)

            send_mail('API DUPLICATE FOUND',
                      'Model: {0}, PK: {1}, VALUE: {2}'.format(str(self.model), self.search_by, key),
                      'Error Logs',
                      [settings.GMAIL_SEND_TO], connection=connection)

        return item.first()

    def get_queryset(self, query, search_by, search_type='__icontains', filters=None):
        if hasattr(self.model, 'is_active'):
            qs = self.model.objects.filter(is_active=True)
        else:
            qs = self.model.objects.all()

        filter_set = filters or {}
        if query:
            if search_by:
                if search_by not in self.search_options.keys():
                    # TODO: Supply an error
                    search_by = None
                else:
                    search_by = self.search_options.get(search_by)
            filter_parameter = (search_by or self.search_by) + search_type
            filter_set.update({filter_parameter: query})

        qs = qs.filter(**filter_set)
        return qs

    def get_serialized_item(self, item, fields):
        validated_fields = self.validate_fields(fields)
        res = {}
        for field in validated_fields:
            value = item.get(field, None)

            try:
                key_name = self.allowed_fields.keys()[self.allowed_fields.values().index(field)]
            except (IndexError, ValueError):
                if '__' in field:
                    key_name = field.split('__')[0]
                else:
                    key_name = field

            res[key_name] = value

        return res

    def get_serialized_qs(self, qs, fields, page=1):
        validated_fields = self.validate_fields(fields)
        try:
            page = int(page)
        except ValueError:
            page = 1

        count = qs.count()
        qs = qs[page*self.limit-self.limit:page*self.limit].values(*validated_fields)
        paginated = []
        for obj in qs:
            item = {}
            for key, value in obj.items():
                try:
                    key_name = self.allowed_fields.keys()[self.allowed_fields.values().index(key)]
                except (IndexError, ValueError):
                    if '__' in key:
                        key_name = key.split('__')[0]
                    else:
                        key_name = key

                item[key_name] = value

            paginated.append(item)

        return {'items': paginated, 'page': page, 'total': count}

    def validate_fields(self, fields):
        validated_fields = []
        for _field in fields:
            field = _field.strip()
            if field in self.allowed_fields.keys():
                if type(self.allowed_fields[field]) is list:
                    validated_fields += self.allowed_fields[field]
                elif type(self.allowed_fields[field]) is str:
                    validated_fields.append(self.allowed_fields[field])

        validated_fields += self.fields
        return set(validated_fields)

    def get_one(self, *args, **kwargs):
        raise NotImplementedError

    def get_list(self, *args, **kwargs):
        raise NotImplementedError

    def get_serialized_item_with_extra(self, qs, fields, *args, **kwargs):
        raise NotImplementedError

    def get_serialized_qs_with_extra(self, qs, fields, *args, **kwargs):
        raise NotImplementedError

    def post(self, request, *args, **kwargs):
        return response(data={'message': 'Method not allowed'}, code=405)

    def put(self, request, *args, **kwargs):
        return response(data={'message': 'Method not allowed'}, code=405)

    def delete(self, request, *args, **kwargs):
        return response(data={'message': 'Method not allowed'}, code=405)
