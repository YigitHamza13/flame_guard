"""Machine-value display labels from the shared JSON catalogs."""
from src.i18n import t, catalog

def label(value):
    key = str(value)
    choices = catalog('en')
    if 'label:' + key in choices:
        return t('label:' + key)
    if 'label:' + key.casefold() in choices:
        return t('label:' + key.casefold())
    return t(key)
