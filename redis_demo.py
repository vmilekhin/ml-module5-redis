import redis
import time
import json

# Подключаемся к локальному Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def simulate_ml_model(text):
    """Имитация тяжелой ML-модели (занимает 2 секунды)"""
    time.sleep(2)
    return {"result": f"Анализ текста: {text}", "model": "resnet18"}

def get_ml_result(user_id, text):
    # 1. RATE LIMITING (не более 3 запросов за 10 секунд)
    rate_key = f"rate:{user_id}"
    requests = r.incr(rate_key)
    if requests == 1:
        r.expire(rate_key, 10) # Устанавливаем TTL 10 секунд
    
    if requests > 3:
        return {"error": "Слишком много запросов! Подождите."}

    # 2. КЭШИРОВАНИЕ (проверяем, есть ли готовый ответ)
    cache_key = f"cache:{text}"
    cached = r.get(cache_key)
    
    if cached:
        print("-> Взято из кэша Redis (быстро)")
        return json.loads(cached)
    
    # Если в кэше нет — считаем модель и сохраняем в Redis на 60 секунд
    print("-> Считаем модель... (долго)")
    result = simulate_ml_model(text)
    r.setex(cache_key, 60, json.dumps(result))
    return result

if __name__ == "__main__":
    user = "user_123"
    query = "Ионные каналы и мембраны"
    
    print("--- Запрос 1 (Промах кэша) ---")
    print(get_ml_result(user, query))
    
    print("\n--- Запрос 2 (Попадание в кэш) ---")
    print(get_ml_result(user, query))
    
    print("\n--- Запрос 3 (Лимит еще не исчерпан) ---")
    print(get_ml_result(user, "Другой текст"))
    
    print("\n--- Запрос 4 (Срабатывает Rate Limit) ---")
    print(get_ml_result(user, "Третий текст"))
