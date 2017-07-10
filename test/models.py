# -*- coding: utf-8 -*-

from django.db import models


class TestModel(models.Model):
    field_1 = models.CharField(max_length=255)

    class Meta:
        managed = False
