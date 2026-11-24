from rest_framework.response import Response
from rest_framework import status

def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    payload = {
        "success": True,
        "message": message,
        "data": data if data is not None else {}
    }
    return Response(payload, status=status_code)

def error_response(message="Error", error=None, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
    payload = {
        "success": False,
        "message": message,
        "error": error
    }
    return Response(payload, status=status_code)
