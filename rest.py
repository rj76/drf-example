import datetime
import logging
import magic
import math

from django.contrib.auth import get_user_model

from django_filters import rest_framework as rest_framework_filters
from drf_extra_fields.fields import Base64FileField
from rest_framework import viewsets, filters, serializers, pagination, renderers, status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import exception_handler
from rest_auth.serializers import PasswordResetSerializer

from drf_renderer_xlsx.renderers import XLSXRenderer


# Get the UserModel
UserModel = get_user_model()

logger = logging.getLogger('apps.core')


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if hasattr(response, 'status_code') and response.status_code != status.HTTP_200_OK:
        print('custom_exception_handler: %s response.' % response.status_code, response.data)
        logger.warning('%s response. reponse data: %s', response.status_code, response.data)

    return response


class RestAuthPasswordResetSerializer(PasswordResetSerializer):
    def get_email_options(self):
        request = self.context.get('request')

        return {
            'domain_override': request.get_host(),
        }


class RestAuthUserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """
    class Meta:
        model = UserModel
        fields = ('pk', 'username', 'email', 'first_name', 'last_name',
                  'sales_user', 'customer_user', 'planning_user', 'engineer',
                  'is_staff', 'is_superuser')
        read_only_fields = ('email', )


def jwt_response_payload_handler(token, user=None, request=None):
    user_type = None
    serialized_user = None

    if hasattr(user, 'sales_user'):
        from apps.company.serializers import SalesUserSerializer
        serialized_user = SalesUserSerializer(user, context={'request': request}).data
        user_type = 'sales_user'

    if hasattr(user, 'customer_user'):
        from apps.company.serializers import CustomerUserSerializer
        serialized_user = CustomerUserSerializer(user, context={'request': request}).data
        user_type = 'customer_user'

    if hasattr(user, 'planning_user'):
        from apps.company.serializers import PlanningUserSerializer
        serialized_user = PlanningUserSerializer(user, context={'request': request}).data
        user_type = 'planning_user'

    if hasattr(user, 'engineer'):
        from apps.company.serializers import EngineerSerializer
        serialized_user = EngineerSerializer(user, context={'request': request}).data
        user_type = 'engineer'

    return {
        'token': token,
        'user': serialized_user,
        'user_type': user_type,
    }


class TransformDatesMixin(object):
    def to_representation(self, instance):
        ret = super(TransformDatesMixin, self).to_representation(instance)
        if 'created' in ret:
            ret['created'] = self.transform_date(ret['created'])

        if 'modified' in ret:
            ret['modified'] = self.transform_date(ret['modified'])

        if 'last_login' in ret and ret['last_login']:
            ret['last_login'] = self.transform_date(ret['last_login'])

        if 'date_joined' in ret and ret['date_joined']:
            ret['date_joined'] = self.transform_date(ret['date_joined'])

        return ret

    def transform_date(self, value):
        if not value:
            return '-'

        if isinstance(value, str):
            try:
                d = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    d = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    return value
        else:
            d = value

        request = self.context.get('request', None)
        if request and 'member' in request.session:
            fmt = request.session['member'].get_setting('date_format')
        else:
            fmt = '%Y/%m/%d'
        s = '%s %%H:%%M' % fmt
        return d.strftime(s)


class My24Pagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000
    _page_size = None

    def paginate_queryset(self, queryset, request, view=None):
        self._page_size = self.get_page_size(request)

        return super().paginate_queryset(queryset, request, view=view)

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                return pagination._positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                pass

        return self.page_size

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'num_pages': math.ceil(self.page.paginator.count / self._page_size),
            'results': data,
        })


class BaseListView(ListAPIView):
    permission_classes = (IsAdminUser,)
    pagination_class = My24Pagination


class BaseViewSet(viewsets.ModelViewSet):
    pass


class RelatedSummaryField(serializers.ReadOnlyField):
    def to_representation(self, value):
        if 'request' not in self.context:
            return ''

        count = value.count()
        model_name = value.model.__name__
        mapping = model_name.lower() + "-list"
        url = reverse(mapping, request=self.context['request'])

        parent_pk = value.instance.pk
        filter_name = list(value.core_filters.keys())[0]

        return dict(
            count=count,
            href="{}?{}={}".format(url, filter_name, parent_pk),
        )


class BaseMy24ViewSet(BaseViewSet):
    """
    Viewset that supports all normal viewset functionality.
    """
    renderer_classes = [renderers.JSONRenderer, renderers.BrowsableAPIRenderer, XLSXRenderer]
    permission_classes = (IsAuthenticated, )
    pagination_class = My24Pagination
    filter_backends = (filters.SearchFilter, rest_framework_filters.DjangoFilterBackend,)

    def is_create(self):
        return self.request.method == 'POST' or (
            self.request.method == 'GET' and 'pk' not in self.kwargs
        )

    def is_update(self):
        return self.request.method == 'PUT' or (self.request.method == 'GET' and 'pk' in self.kwargs)

    def is_list(self):
        if self.request.method == 'POST':
            return False

        if self.request.method == 'GET' and 'pk' in self.kwargs:
            return False

        return True


class My24Base64FileField(Base64FileField):
    ALLOWED_TYPES = ('xls', 'doc', 'pdf', 'xlsx', 'docx', 'txt', 'odt', 'zip', 'png', 'jpg', 'gif')

    def get_file_extension(self, filename, decoded_file):
        filetype = magic.from_buffer(decoded_file, mime=True).lower()

        if filetype == 'application/vnd.ms-office':
            return 'xls'

        if filetype == 'application/msword':
            return 'doc'

        if filetype == 'application/pdf':
            return 'pdf'

        if filetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            return 'xlsx'

        if filetype == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return 'docx'

        if filetype == 'text/plain':
            return 'txt'

        if filetype == 'application/vnd.oasis.opendocument.text':
            return 'odt'

        if filetype == 'application/zip':
            return 'zip'

        if filetype == 'image/png':
            return 'png'

        if filetype == 'image/jpeg':
            return 'jpg'

        if filetype == 'image/gif':
            return 'gif'

        return None
