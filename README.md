# django-tiny-rest-api
A small app to help build REST API on top of Django Web framework


Usage:

```python auth.py
Add Token model
``

```python example.py
from api.restframework.views import APIView
from api.restframework.utils import response


class AirportAPIView(APIView):
    model = Airport
    fields = ['icao', 'iata', 'name', 'time_zone']
    extra_fields = ['sunrise', 'sunset', 'time_shift']
    search_by = 'icao'
    search_options = {
        'icao': 'icao',
        'iata': 'iata',
        'name': 'name',
        'country': 'country__name',
        'city': 'city__name'
    }
    allowed_fields = {
        'coords': ['latitude', 'longitude'],
        'phone': 'phone',
        'fax': 'fax',
        'email': 'email',
        'website': 'website',
        'country': 'country__name',
        'city': 'city__name',
        'tower_hours': 'tower_hours',
        'pcn': 'pcn',
    }

    def get_one(self, request, icao):
        fields = self.get_fields(request)
        additional_fields = fields[:]
        additional_fields.append('time_zone')
        additional_fields.append('coords')
        item = self.get_object(icao)
        if item is None:
            return response({'message': 'Not found'}, 404)
        serialized_item = self.get_serialized_item(item, additional_fields)
        res = self.get_serialized_item_with_extra(serialized_item, fields)
        return response(res)

    def get_list(self, request):
        query = request.GET.get('query')
        search_by = request.GET.get('search_by')
        page = request.GET.get('page', 1)
        fields = self.get_fields(request)

        qs = self.get_queryset(query, search_by)
        additional_fields = fields[:]
        additional_fields.append('time_zone')
        additional_fields.append('coords')
        serialized_qs = self.get_serialized_qs(qs, additional_fields, page)
        res = self.get_serialized_qs_with_extra(serialized_qs, fields)
        return response(res)

    def get_serialized_item_with_extra(self, obj, fields, *args, **kwargs):
        requested_extra = list(set(self.extra_fields).intersection(fields))
        for ef in requested_extra:
            time = Time(obj['time_zone'], obj['longitude'], obj['latitude'])
            if ef == 'sunrise':
                obj['sunrise'] = time.get_sunrise()
            elif ef == 'sunset':
                obj['sunset'] = time.get_sunset()
            elif ef == 'time_shift':
                obj['time_shift'] = time.utc_offset().get('repr')

        if 'coords' not in fields:
            if 'latitude' in obj:
                del obj['latitude']
            if 'longitude' in obj:
                del obj['longitude']

        if 'time_zone' in obj:
            del obj['time_zone']

        return obj

    def get_serialized_qs_with_extra(self, qs, fields, *args, **kwargs):
        for obj in qs['items']:
            obj = self.get_serialized_item_with_extra(obj, fields)

        return qs
```