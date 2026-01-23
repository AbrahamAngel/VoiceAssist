from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import redirect

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({"success": True})  # AJAX OK
        else:
            return JsonResponse({"success": False}, status=401)

    return JsonResponse({"error": "POST required"}, status=400)


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({"success": True})

    return JsonResponse({"error": "POST required"}, status=400)
