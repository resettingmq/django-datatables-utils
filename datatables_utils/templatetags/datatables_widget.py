# -*- coding: utf-8 -*-

from django.template import Library
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder
import json

register = Library()


@register.inclusion_tag('dt_templates/dt_tabel.html')
def render_table(dt_config, class_=None):
    titles = dt_config.get_titles()
    return {'dt_config': dt_config, 'titles': titles, 'class': class_}


@register.inclusion_tag('dt_templates/dt_jsscript.html')
def render_js_script(dt_config):
    return {'dt_config': dt_config}


@register.filter(name='json')
def json_filter(value):
    return mark_safe(json.dumps(value, cls=DjangoJSONEncoder))


@register.simple_tag(takes_context=True)
def detail_url(context, id_identifier):
    """
    : 这个template tag依赖于dt_config context，并且dt_config具有detail_url_format属性(str)
    : DataTablesMixin中重写了get_context_data()方法，将dt_config加入了context中
    :param context: 
    :param detail_id: 
    :return: 
    """
    detail_url_format = context['dt_config'].detail_url_format
    tokens = detail_url_format.split('{}', 1)
    tokens = ['"{}"'.format(token) for token in tokens]
    tokens.insert(1, id_identifier)
    return mark_safe(' + '.join(tokens))
