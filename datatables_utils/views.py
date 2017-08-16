from functools import reduce
from django.views import generic
from django.http import JsonResponse
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.utils.module_loading import import_string

from .utils import ModelDataTable


class JsonContextMixin:
    def get_json_context_data(self, **kwargs):
        """
        : 生成JsonResponse的数据
        :param kwargs: 需要添加进返回值的键值对
        :return: dict, JsonResponse的数据
        """
        return kwargs


class JsonResponseMixin:
    json_response_class = JsonResponse

    def render_to_json_response(self, context, **response_kwargs):
        """
        : 生成JsonResonse对象并返回
        :param context: JsonResponse对象所包含的data
        :param response_kwargs: JsonResponse对象初始化所需要的其他参数，可为空
        :return: 所生成的JsonResponse对象
        """
        return self.json_response_class(context, **response_kwargs)


class DataTablesMixin(JsonResponseMixin, JsonContextMixin):
    """
    : 这个Mixin不应该被单独使用，它依赖与定义了get_context_data()的类
    """
    dt_data_src = 'data'
    dt_config = None
    dt_column_fields = None
    dt_table_name = None

    def get_dt_data_src(self):
        return self.dt_data_src

    def get_dt_config(self):
        if self.dt_config is None:
            raise ImproperlyConfigured('ModelDataTables is not properly setted in DataTablesMixin')
        return self.dt_config

    def get_dt_table_name(self):
        if self.dt_table_name is not None:
            return self.dt_table_name
        dt_config = self.get_dt_config()
        return self.dt_config.table_id

    def is_server_side(self):
        return bool(self.dt_config.dt_serverSide)

    def get_dt_query_fields(self):
        """
        : 生成DataTables实例所期望的model field names集合
        :return: list, model field names 列表
        """
        # if self.dt_column_fields is not None:
        #     return self.dt_column_fields
        # try:
        #     model = self.get_queryset().model
        #     dt_column_fields = model.DataTablesMeta.column_fields.keys()
        # except AttributeError:
        #     return []
        # else:
        #     return dt_column_fields
        return self.dt_config.get_query_fields()

    def process_http_queryset(self, queryset):
        pass

    def get_json_context_data(self, http_queryset=None):
        """
        : 依赖于其他class的get_queryset()方法
        : 包含了数据获取，处理的逻辑
        :return: dict
        """
        json_context = {}

        self.process_http_queryset(http_queryset)
        dt_column_fields = self.get_dt_query_fields()
        queryset = self.get_queryset()
        if self.is_server_side():
            if http_queryset is None:
                raise ValueError('No GET queryset passed in for server-side mode')

            try:
                draw = int(http_queryset.get('draw'))
            except ValueError:
                json_context.update(error='Invalid request arguments')
                return super().get_json_context_data(**json_context)
            else:
                json_context.update(draw=draw)
            records_total = queryset.count()
            json_context.update(recordsTotal=records_total)

            # 处理filter
            # 只实现了对全局的搜索
            # 没有实现对指定列的搜索
            pattern = http_queryset.get('search[value]')
            is_regex = http_queryset.get('search[regex]') == 'true'
            queryset = queryset.filter(
                reduce(
                    lambda x, y: x | y,
                    [c.get_filter_q_object(pattern, is_regex) for c in self.dt_config.columns.values()]
                )
            )
            records_filtered = queryset.count()
            json_context.update(recordsFiltered=records_filtered)

            # 处理order
            order_dir = '' if http_queryset['order[0][dir]'] == 'asc' else '-'
            order_column = list(self.dt_config.columns.values())[int(http_queryset['order[0][column]'])].name
            queryset = queryset.order_by(order_dir + order_column)

            # 处理分页
            page_start = int(http_queryset['start'])
            page_length = int(http_queryset['length'])
            queryset = queryset[page_start:page_start + page_length]

        json_context[self.dt_data_src] = list(queryset.values(*dt_column_fields))

        return super().get_json_context_data(**json_context)

    def get_context_data(self, **kwargs):
        """
        : 将ModelDataTables类添加进context
        : 需要依赖与其他class或者mixin
        :param dt_config: 指定外部的ModelDataTables类
        :param kwargs: 额外的命名参数
        :return: context
        """
        if 'dt_config' not in kwargs:
            kwargs['dt_config'] = self.get_dt_config()

        return super().get_context_data(**kwargs)


class ModelDataTablesMixin(DataTablesMixin):
    """
    根据self.model中的相关属性配置DataTablesMixin属性
    注意是动态生成，每次请求都应该被调用，
    包括ajax请求
    """
    def config_datatables_from_model(self, dt_config=None):
        if self.dt_config is not None:
            return
        try:
            datatables_class = self.model.datatables_class
        except AttributeError:
            raise ImproperlyConfigured('No datatables class configured in {}:{}'
                                       .format(self.model._meta.app_label, self.model._meta.verbose_name))
        if isinstance(datatables_class, str):
            try:
                datatables_class = import_string(datatables_class)
            except ImportError:
                raise ImproperlyConfigured('Error in datatables configured in {}:{}'
                                           .format(self.model._meta.app_label, self.model._meta.verbose_name))
        if not issubclass(datatables_class, ModelDataTable):
            raise ImproperlyConfigured('Improperly configured datatables_class attr in {}:{}'
                                       .format(self.model._meta.app_label, self.model._meta.verbose_name))
        self.dt_config = datatables_class

    def get_context_data(self, **kwargs):
        # 注意：这里也需要对kwargs中的dt_config参数进行判断
        # 这样才能够与DatatablesMixin统一
        # 同时在子类中才能够控制self.dt_config的生成获取
        if 'dt_config' not in kwargs:
            self.config_datatables_from_model()
        return super().get_context_data(**kwargs)

    def get_json_context_data(self, *args, **kwargs):
        self.config_datatables_from_model()
        return super().get_json_context_data(*args, **kwargs)


class DataTablesListView(ModelDataTablesMixin, generic.ListView):

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            # if not self.dt_config.dt_serverSide:
            return self.render_to_json_response(self.get_json_context_data(request.GET))
        return super().get(request, *args, **kwargs)
