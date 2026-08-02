import json
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from .models import wheater
from .password import hash_password, pass_check
from .serializer import wheaterserializer
from django.conf import settings
from functools import wraps
import logging

logger = logging.getLogger(__name__)


WEATHER_API_KEY = settings.WEATHERAPI_KEY
WEATHER_API_URL = "https://api.weatherapi.com/v1"

def welcome(request):
    return render(request, "index.html")


def logged_in(request):
    return bool(request.session.get("weather_user_id"))


def require_login(view_function):
    @wraps(view_function)
    def wrapper(request, *args, **kwargs):
        if not logged_in(request):
            login_url = reverse("login")
            return redirect(f"{login_url}?next={request.get_full_path()}")

        return view_function(request, *args, **kwargs)

    return wrapper


@ensure_csrf_cookie
@require_login
def city(request):
    return render(request, "city.html")


@require_POST
def fetch_city(request):
    if not logged_in(request):
        return JsonResponse(
            {
                "error": "Login required",
                "login_url": reverse("login")
            },
            status=401
        )

    try:
        data = json.loads(request.body)
        city = data.get("city", "").strip()
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request data"}, status=400)

    if len(city) < 2:
        return JsonResponse({"res": []})

    try:
        response = requests.get(
            f"{WEATHER_API_URL}/search.json",
            params={"key": WEATHER_API_KEY, "q": city},
            timeout=10
        )
        response.raise_for_status()
        return JsonResponse({"res": response.json()})

    except requests.RequestException:
        return JsonResponse(
            {"error": "Could not fetch city suggestions"},
            status=503
        )


@require_login
def city_weather(request):
    city = request.GET.get("city", "").strip()

    if not city:
        return redirect("city")

    try:
        response = requests.get(
            f"{WEATHER_API_URL}/current.json",
            params={"key": WEATHER_API_KEY, "q": city},
            timeout=10
        )
        response.raise_for_status()

        weather_data = response.json()

        if "error" in weather_data:
            return render(request, "city.html", {
                "error": weather_data["error"]["message"]
            })

    except requests.RequestException:
        return render(request, "city.html", {
            "error": "Weather service is unavailable. Please try again."
        })

    user = wheater.objects.filter(
        id=request.session["weather_user_id"]
    ).first()

    email_sent = False

    if user and user.email:
        email_sent = send_weather_email(user.email, weather_data)

    return render(request, "details.html", {
        "weather": weather_data,
        "email_sent": email_sent
    })


def send_weather_email(email, weather):
    location = weather["location"]
    current = weather["current"]

    subject = f"WeatherX: {location['name']} weather update"

    message = f"""
WeatherX update for {location['name']}, {location['country']}

Condition: {current['condition']['text']}
Temperature: {current['temp_c']} C
Feels like: {current['feelslike_c']} C
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h
Pressure: {current['pressure_mb']} mb

Stay prepared,
WeatherX
"""

    try:
        sent_count = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return sent_count == 1

    except Exception:
        logger.exception("Weather email failed for %s", email)
        return False


def login(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        next_url = request.POST.get("next") or request.GET.get("next")

        try:
            user = wheater.objects.get(email__iexact=email)

            if not pass_check(password, user.password):
                return render(request, "login.html", {
                    "error": "Invalid email or password",
                    "next": next_url
                })

            request.session.cycle_key()
            request.session["weather_user_id"] = user.id

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()}
            ):
                return redirect(next_url)

            return redirect("city")

        except wheater.DoesNotExist:
            return render(request, "login.html", {
                "error": "Invalid email or password",
                "next": next_url
            })

    return render(request, "login.html", {
        "next": request.GET.get("next", "")
    })


def register(request):
    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if password != confirm_password:
            return render(request, "register.html", {
                "error": "Passwords do not match"
            })

        data = request.POST.copy()
        data["email"] = data.get("email", "").strip().lower()
        data["password"] = hash_password(password)

        serializer = wheaterserializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return redirect("login")

        return render(request, "register.html", {
            "errors": serializer.errors
        })

    return render(request, "register.html")


def logout(request):
    request.session.flush()
    return redirect("login")