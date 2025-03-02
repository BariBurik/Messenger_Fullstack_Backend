from django.http import JsonResponse


def delete_http_only_cookie(request):
    response = JsonResponse({"message": "HttpOnly cookie deleted"})
    response.delete_cookie('access-token', path='/')
    response.delete_cookie('refresh-token', path='/')
    return response