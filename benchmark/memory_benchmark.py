# benchmark/memory_benchmark.py
import psutil

def measure_memory():
    process = psutil.Process()
    mem = process.memory_info().rss  # в байтах
    print(f"Current memory usage: {mem / 1024 ** 2:.2f} MB")

if __name__ == "__main__":
    measure_memory()