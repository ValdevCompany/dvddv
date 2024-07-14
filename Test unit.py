import requests
import time

# URL вашего веб-приложения Flask
url = 'http://127.0.0.1:8080'

# Количество запросов для тестирования
num_requests = 100

# Список для сохранения времени отклика каждого запроса
response_times = []

# Отправляем num_requests запросов и измеряем время отклика для каждого
for _ in range(num_requests):
    start_time = time.time()
    response = requests.get(url)
    end_time = time.time()
    response_time = end_time - start_time
    response_times.append(response_time)
    print(f"Response time: {response_time} seconds")

# Вычисляем среднее время отклика
average_response_time = sum(response_times) / len(response_times)
print(f"Average response time: {average_response_time} seconds")

