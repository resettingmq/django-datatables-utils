from functools import reduce
from django.views import generic
from django.http import JsonResponse
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation


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

    def get_json_context_data(self, http_queryset=None):
        """
        : 依赖于其他class的get_queryset()方法
        : 包含了数据获取，处理的逻辑
        :return: dict
        """
        json_context = {}

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

    def get_context_data(self, dt_config=None, **kwargs):
        """
        : 将ModelDataTables类添加进context
        : 需要依赖与其他class或者mixin
        :param dt_config: 指定外部的ModelDataTables类
        :param kwargs: 额外的命名参数
        :return: context
        """
        datatables_config = dt_config if dt_config is not None else self.get_dt_config()
        datatables_id = datatables_config.table_id
        kwargs.update(
            dt_config=datatables_config,
            dt_id=datatables_id
        )
        return super().get_context_data(**kwargs)


class DataTablesListView(DataTablesMixin, generic.ListView):

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            # if not self.dt_config.dt_serverSide:
                return self.render_to_json_response(self.get_json_context_data(request.GET))
        return super().get(request, *args, **kwargs)
