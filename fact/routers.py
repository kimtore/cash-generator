# -*- coding: utf-8 -*-

def get_db_name(model):
    if model.__name__ == 'Invoice' or model.__name__ == 'Transaction' \
            or model.__name__ == 'Entry' or model.__name__ == 'TaxtableEntry' \
            or model.__name__ == 'Customer' or model.__name__ == 'Job' \
            or model.__name__ == 'Term' or model.__name__ == 'Slot' \
            or model.__name__ == 'Split':
        return 'gnucash'
    return 'default'

class FactRouter(object):
    def db_for_read(self, model, **hints):
        return get_db_name(model)

    def db_for_write(self, model, **hints):
        return get_db_name(model)

