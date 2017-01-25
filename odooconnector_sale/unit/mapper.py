# -*- encoding: utf-8 -*-
# Copyright (C) 2004-Today Simplify Solutions. All Rights Reserved

import logging
from openerp.addons.connector.unit.mapper import (ExportMapChild,
                                                  ImportMapChild,
                                                  ImportMapper,
                                                  mapping)


_logger = logging.getLogger(__name__)


class OdooExportMapSaleChild(ExportMapChild):

    def format_items(self, item_values):
        items = super(OdooExportMapSaleChild, self).format_items(
            item_values
        )
        item_list = []
        for each in items:
            if each.get('line_id'):
                item_list.append((1, each.get('line_id'), each))
            else:
                item_list.append((0, 0, each))
        print"item_listitem_list", item_list
        return item_list


class OdooImportMapSaleChild(ImportMapChild):

    def format_items(self, item_values):
        print"item_valuesitem_valuesitem_values", item_values
        item_list = []
        if item_values:
            for each in item_values:
                if each.get('line_id'):
                    item_list.append((1, each.get('line_id'), each))
                else:
                    item_list.append((0, 0, each))
        else:
            item_list = [(5, 0)]
        print"item_listitem_list", item_list
        return item_list
