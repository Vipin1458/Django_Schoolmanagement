# In core/utils.py
from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data['status_code'] = response.status_code
    return response

# settings.py
REST_FRAMEWORK['EXCEPTION_HANDLER'] = 'core.utils.custom_exception_handler'
