import requests
from django.shortcuts import render
from .forms import CityForm
from datetime import datetime
from collections import defaultdict
from statistics import mean


def dashboard(request):
    weather_data = None
    forecast_data = None
    hourly_data = []
    api_key = 'b58b35d5841969ff4987d7e58ed9cbad'
    form = CityForm()

    # 🔹 Initialize session history
    if 'search_history' not in request.session:
        request.session['search_history'] = []

    current_data = {}
    forecast_json = {}

    # 🔸 Handle City Search via POST
    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            city = form.cleaned_data['city']

            # Save city in session history (no duplicates)
            history = request.session.get('search_history', [])
            if city not in history:
                history.insert(0, city)
                request.session['search_history'] = history[:10]  # max 10 cities

            current_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"

            current_data = requests.get(current_url).json()
            forecast_json = requests.get(forecast_url).json()

    # 🔸 Handle Geolocation via GET
    elif request.method == 'GET' and request.GET.get('lat') and request.GET.get('lon'):
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')

        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"

        current_data = requests.get(current_url).json()
        forecast_json = requests.get(forecast_url).json()

    # 🔹 Process Current Weather Data
    if current_data.get('cod') == 200:
        weather_data = {
            'city': f"{current_data['name']}, {current_data['sys']['country']}",
            'temperature': current_data['main']['temp'],
            'description': current_data['weather'][0]['description'].capitalize(),
            'icon': current_data['weather'][0]['icon'],
            'feels_like': current_data['main']['feels_like'],
            'temp_min': current_data['main'].get('temp_min', current_data['main']['temp']),
            'temp_max': current_data['main'].get('temp_max', current_data['main']['temp']),
            'humidity': current_data['main']['humidity'],
            'pressure': current_data['main']['pressure'],
            'wind_speed': current_data['wind']['speed'],
            'wind_deg': current_data['wind']['deg'],
            'visibility': current_data.get('visibility', 0),
            'sunrise': datetime.fromtimestamp(current_data['sys']['sunrise']).strftime('%I:%M %p'),
            'sunset': datetime.fromtimestamp(current_data['sys']['sunset']).strftime('%I:%M %p'),
            'lat': current_data['coord']['lat'],
            'lon': current_data['coord']['lon'],
        }

    # 🔹 Process 5-Day Forecast & Hourly Data
    if forecast_json.get('cod') == "200":
        forecast_by_date = defaultdict(list)

        for item in forecast_json['list']:
            dt = datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S')
            date_key = dt.date()
            forecast_by_date[date_key].append(item)

            # Collect hourly chart data (first 8 × 3-hour blocks = 24 hours)
            if len(hourly_data) < 8:
                hourly_data.append({
                    'time': dt.strftime('%I %p'),
                    'temp': item['main']['temp']
                })

        forecast_data = []
        for date, items in forecast_by_date.items():
            temps = [entry['main']['temp'] for entry in items]
            descriptions = [entry['weather'][0]['description'].capitalize() for entry in items]
            icons = [entry['weather'][0]['icon'] for entry in items]

            forecast_data.append({
                'date': date.strftime('%A, %b %d'),
                'temp_min': round(min(temps), 1),
                'temp_max': round(max(temps), 1),
                'temp_avg': round(mean(temps), 1),
                'description': descriptions[0],
                'icon': icons[0],
            })

        forecast_data = forecast_data[:5]  # Only next 5 days

    # 🔚 Final Render
    return render(request, 'app1/dashboard.html', {
        'form': form,
        'weather_data': weather_data,
        'forecast_data': forecast_data,
        'hourly_data': hourly_data,
        'search_history': request.session.get('search_history', [])
    })
