# django-datatables-utils
A simple utils for django-datatables integration.

- [示例 examples](http://demo.resettingmq.top/datatables/)

- [应用项目](http://django.resettingmq.top/client/)

安装
--------------

将datatables_utils包复制到项目文件夹下，并将datatables_utils添加到INSTALLED_APPS中。

开始
--------------

> 为了能使DataTables正常工作，需要在项目正确导入DataTables所依赖的javascript和css文件

1. 建立需要通过DataTables展示数据的Model
```python
from django.db import models

class Client(models.Model):
    name = models.CharField('客户名称', max_length=32)
    tel = models.CharField('电话', max_length=16)
    email = models.CharField('电子邮箱', max_length=64)
```

2. 通过声明的方式建立DataTables配置类
```python
form datatables_utils.utils import ModelDataTable

class SimpleClientDataTable(ModelDataTable):
    class Meta:
        model = Client
        fields = ['name', 'tel', 'email']
```

3. 建立并配置View
```python
from datatables_utils.views import DataTablesListView

class ClientListView(DataTablesListView):
    model = Client
    dt_config = SimpleClientDataTable
    template_name = 'client_list.html'
```

4. 在template中采用datatables_utils的template tags渲染数据表以及javascript代码。
```HTML
{% extends 'some_base.html' %}

{% load datatables_widget %}

{% block content %}
	{% render_table dt_config %}
{% endblock content %}

{% block javascript %}
	{% render_js_script dt_config %}
{% endblock javascript %}
```

> 注意：render_js_script template tag的调用需要发生在jquery.js, datatables相关javascript代码导入之后。


选项
--------------

在Django Datatables utils中，可以通过在`Meta`指定部分用于初始化Datatables的选项，也可以通过DatatablesColumn对象设置。

### `width`选项

可以通过`width`选项设置每列的宽度。

```python
class ClientDataTable(ModelDataTable):
    class Meta:
        model = Client
        fields = ['name', 'tel', 'email']
        width = {
            'name': '200px';
        }
```

或者：

```python
from datatables_utils.utils import DatatablesColumn

class ClientDataTable(ModelDataTable):
    name = DatatablesColumn(width='200px')

    class Meta:
        model = Client
        fields = ['tel', 'email']
```

### `searchable`选项

可以通过`searchable`选项设置某列是否可以被搜索。

默认对每列都是可搜索的。

```python
class ClientDataTable(ModelDataTable):
    tel = DatatablesColumn(searchable=False)

    class Meta:
        model = Client
        fields = ['name', 'email']
```

> todo: 能够通过`Meta`设置`searchable`

### `orderable`选项

通过`orderable`选项，能够设置是否可以通过某列来进行排序。

默认对每一列都可进行排序操作。

```python
class ClientDataTable(ModelDataTable):
    email = DatatablesColumn(orderable=False)

    class Meta:
        model = Client
        fields = ['name', 'tel']
```

> todo: 能够通过`Meta`设置`orderable`

### `title`选项

通过`title`选项，能够设置每列表头显示的内容。

默认情况下，`title`的值为对应`Model Field.verbose_name`属性的值。

```python
class ClientDataTable(ModelDataTable):
    class Meta:
        model = Client
        fields = ['name', 'tel', 'email']
        titles = {
            'name': "Client's full name"
        }
```

或者：

```python
class ClientDataTable(ModelDataTable):
    name = DatatablesColumn(title="Client's full name")

    class Meta:
        model = Client
        fields = ['tel', 'email']
```

### `column_order`选项

Django-Datatable-Utils默认先显示`DatatablesColumn`声明的列（按照声明的顺序），再显示`Meta.fields`中指定的列（按照指定顺序）。
要改变默认顺序，可以通过`column_order`选项实现。

```python
class ClientDataTable(ModelDatatable):
    tel = DatatablesColumn()

    class Meta:
        model = Client
        fields = ['name', 'email']
        column_order = ['email', 'name', 'tel']
    
```

### `detail_url_format`选项

有些情况下，我们还希望在点击每一行的时候能够跳转到相应项目的详细页面。

可以通过设置`detail_url_format`选项来实现这个功能。

这个选项要求其中包含一个占位符("{}")，用来表示`detail_url`中`object_id`的位置。例如:


```python
class ClientDataTable(ModelDataTable):
    class Meta:
        model = Client
        fields = ['name', 'tel', 'email']
        detail_url_format = '/detail/url/to/client/{}' ```
```

> 注意：这个选项需要配合`dt_rowId`选项使用。

### `dt_rowId`选项(类属性)

`dt_rowId`选项用于指定ORM对象中作为唯一标识的属性名称。

默认为`dt_rowId = 'pk'`。

```python
class ClientDataTable(ModelDataTable):
    dt_rowId = 'slug_field_name'
    
    class Meta:
        model = Client
        fields = ['name', 'tel', 'email']
```

### `dt_serverSide`选项(类属性)

用于设置Datatables是否工作于`server side`模式。

默认为`True`。

### `dt_ajax`选项(类属性)

用于指定ajax请求的目标地址。

默认为`dt_ajax = './'`(即向当前页面请求)。
