from datatables_utils.utils import ModelDataTable, DataTablesColumn
from . import models as test_models


class DeclaredModelDataTable(ModelDataTable):
    field_1 = DataTablesColumn()
    field_not_exist_1 = DataTablesColumn()

    class Meta:
        model = test_models.TestModel


class WithMetaModelDataTable(ModelDataTable):
    class Meta:
        model = test_models.TestModel
        fields = ['field_1', 'field_not_exist_1']
