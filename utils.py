from django.http import JsonResponse


def successful(code):
    """
    Check if http-code is successful.
    Args:
        code: Http code e.g. 200, 206, 403, 500 etc.

    Returns:
        True if code is in range 200 - 300, False otherwise
    """
    return code // 100 == 2


def response(data, code=200):
    if not successful(code):
        return JsonResponse({'error': data}, status=code)
    else:
        return JsonResponse(data, status=code)
