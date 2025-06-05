 #benchmark/latency_test.py
import time

def measure_latency():
    start = time.time()
    # TODO: заменить на реальный HTTP/RAG/DB-запрос
    time.sleep(0.1)
    end = time.time()
    print(f"Latency: {end - start:.3f} seconds")

if __name__ == "__main__":
    measure_latency()