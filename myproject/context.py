from django.http import HttpResponse


def get_context(request):
    response = HttpResponse()
    return {
        "request": request,
        "response": response
    }