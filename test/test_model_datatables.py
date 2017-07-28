# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured

from datatables_utils.utils import ModelDataTable, DataTablesColumn

from .models import TestModel
from . model_datatables import DeclaredModelDataTable


class ModelDataTableTestCase(TestCase):
    """
    Testcase for testing ModelDataTable
    """

    def test_modeldatatable_class_with_no_meta_defined(self):
        with self.assertRaises(ImproperlyConfigured):
            class WithNoMetaModelDataTable(ModelDataTable):
                pass

    def test_modeldatatables_class_with_no_model_defiled(self):
        with self.assertRaises(ImproperlyConfigured):
            class WithNoModelDefinedModelDataTable(ModelDataTable):
                class Meta:
                    not_model = 'some str'

    def test_get_field_from_declaration(self):
        declared_columns = DeclaredModelDataTable._declared_columns
        columns = DeclaredModelDataTable.columns
        meta_defined_columns = DeclaredModelDataTable._meta_defined_columns
        self.assertIn('field_1', declared_columns)
        self.assertIn('field_1', columns)
        self.assertNotIn('field_not_exist_1', declared_columns)
        self.assertNotIn('field_not_exist_1', columns)

        self.assertNotIn('field_1', meta_defined_columns)
        self.assertNotIn('field_not_exist_1', meta_defined_columns)

    def test_get_field_from_meta(self):
        pass

    def test_datatablescolumn_initial_properly(self):
        dt_column = DeclaredModelDataTable.columns['field_1']
        self.assertTrue(isinstance(dt_column, DataTablesColumn))

    def test_datatablescolumn_ref_modelfiled_properly(self):
        dt_column = DeclaredModelDataTable.columns['field_1']
        model_defiend_field = TestModel._meta.get_field('field_1')
        self.assertIs(dt_column._field, model_defiend_field)

    def test_get_default_pk_column(self):
        pk_column = DeclaredModelDataTable.pk_column
        model_id_field = TestModel._meta.get_field('id')
        self.assertIs(pk_column._field, model_id_field)
