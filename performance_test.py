import asyncio
import sqlite3
import time
import statistics
import os
from datetime import datetime
from validators import validate_group_name, validate_conf_date, validate_url

# Налаштування
DB_NAME = 'conference_bot.db'
CONCURRENT_USERS = [10, 30, 50, 100]  # Різні рівні навантаження
REQUESTS_PER_USER = 10


def check_db_exists():
    if not os.path.exists(DB_NAME):
        print(f"❌ Помилка: Файл бази даних '{DB_NAME}' не знайдено!")
        print("Спочатку запустіть database_create.py")
        return False
    return True


# Функції тестування (імітація роботи бота)
def test_get_user_role(user_id):
    """TC-001: Перевірка ролі користувача (READ операція)"""
    start_time = time.perf_counter()
    try:
        conn = sqlite3.connect(DB_NAME, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE tg_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        elapsed = time.perf_counter() - start_time
        return {
            'success': result is not None,
            'response_time': elapsed * 1000,  # в мілісекундах
            'operation': 'get_user_role'
        }
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        return {
            'success': False,
            'response_time': elapsed * 1000,
            'operation': 'get_user_role',
            'error': str(e)
        }


def test_create_group(group_name):
    """TC-002: Створення групи (WRITE операція)"""
    start_time = time.perf_counter()
    try:
        if not validate_group_name(group_name):
            elapsed = time.perf_counter() - start_time
            return {
                'success': False,
                'response_time': elapsed * 1000,
                'operation': 'create_group',
                'error': 'Validation failed'
            }

        conn = sqlite3.connect(DB_NAME, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
        conn.commit()
        conn.close()

        elapsed = time.perf_counter() - start_time
        return {
            'success': True,
            'response_time': elapsed * 1000,
            'operation': 'create_group'
        }
    except sqlite3.IntegrityError:
        # Група вже існує
        elapsed = time.perf_counter() - start_time
        return {
            'success': False,
            'response_time': elapsed * 1000,
            'operation': 'create_group',
            'error': 'Group already exists'
        }
    except sqlite3.OperationalError as e:
        # Database locked
        elapsed = time.perf_counter() - start_time
        return {
            'success': False,
            'response_time': elapsed * 1000,
            'operation': 'create_group',
            'error': 'Database locked'
        }
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        return {
            'success': False,
            'response_time': elapsed * 1000,
            'operation': 'create_group',
            'error': str(e)
        }


def test_create_conference(i):
    """TC-003: Створення конференції (WRITE операція з валідацією)"""
    start_time = time.perf_counter()

    topic = f"Test Conference {i}_{int(time.time())}"
    conf_date = "25.12.2025"
    conf_time = "14:00"
    link = f"https://zoom.us/j/{100000 + i}"

    try:
        if not (3 <= len(topic) <= 100):
            elapsed = time.perf_counter() - start_time
            return {'success': False, 'response_time': elapsed * 1000,
                    'operation': 'create_conference', 'error': 'Invalid topic'}

        if not validate_conf_date(conf_date):
            elapsed = time.perf_counter() - start_time
            return {'success': False, 'response_time': elapsed * 1000,
                    'operation': 'create_conference', 'error': 'Invalid date'}

        if not validate_url(link):
            elapsed = time.perf_counter() - start_time
            return {'success': False, 'response_time': elapsed * 1000,
                    'operation': 'create_conference', 'error': 'Invalid URL'}

        conn = sqlite3.connect(DB_NAME, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conferences (topic, conf_date, conf_time, link, group_id) VALUES (?, ?, ?, ?, ?)",
            (topic, conf_date, conf_time, link, 1)
        )
        conn.commit()
        conn.close()

        elapsed = time.perf_counter() - start_time
        return {
            'success': True,
            'response_time': elapsed * 1000,
            'operation': 'create_conference'
        }
    except sqlite3.OperationalError as e:
        elapsed = time.perf_counter() - start_time
        return {
            'success': False,
            'response_time': elapsed * 1000,
            'operation': 'create_conference',
            'error': 'Database locked'
        }
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        return {
            'success': False,
            'response_time': elapsed * 1000,
            'operation': 'create_conference',
            'error': str(e)
        }


# Логіка тестування
async def run_single_user_scenario(user_id, iteration):
    """Один віртуальний користувач виконує сценарій"""
    results = []
    loop = asyncio.get_running_loop()

    # 1. Перевірка ролі (READ)
    result = await loop.run_in_executor(None, test_get_user_role, user_id)
    results.append(result)
    await asyncio.sleep(0.1)  # Think time

    # 2. Створення групи (WRITE)
    group_name = f"TestGroup_{user_id}_{iteration}_{int(time.time() * 1000)}"
    result = await loop.run_in_executor(None, test_create_group, group_name)
    results.append(result)
    await asyncio.sleep(0.2)  # Think time

    # 3. Створення конференції (WRITE)
    result = await loop.run_in_executor(None, test_create_conference,
                                        user_id * 1000 + iteration)
    results.append(result)

    return results


async def run_load_test(num_users, requests_per_user):
    """Запуск навантажувального тесту"""
    print(f"\n{'=' * 70}")
    print(f"🚀 ЗАПУСК ТЕСТУ: {num_users} одночасних користувачів")
    print(f"{'=' * 70}")

    all_results = []
    start_time = time.time()

    # Користувачі з БД
    user_ids = [101, 201, 301, 401, 501]

    # Створюємо задачі для всіх користувачів
    tasks = []
    for i in range(num_users):
        user_id = user_ids[i % len(user_ids)]
        for iteration in range(requests_per_user):
            tasks.append(run_single_user_scenario(user_id, iteration))

    # Виконуємо всі задачі паралельно
    results_list = await asyncio.gather(*tasks)

    # Збираємо всі результати
    for results in results_list:
        all_results.extend(results)

    end_time = time.time()
    total_time = end_time - start_time

    # Аналіз результатів

    # Розділяємо по операціях
    by_operation = {}
    for result in all_results:
        op = result['operation']
        if op not in by_operation:
            by_operation[op] = []
        by_operation[op].append(result)

    print(f"\n📊 РЕЗУЛЬТАТИ ТЕСТУВАННЯ")
    print(f"{'─' * 70}")

    # Загальна статистика
    total_requests = len(all_results)
    successful = sum(1 for r in all_results if r['success'])
    failed = total_requests - successful
    error_rate = (failed / total_requests * 100) if total_requests > 0 else 0

    print(f"\n✅ Загальна кількість запитів: {total_requests}")
    print(f"✅ Успішні запити: {successful} ({100 - error_rate:.1f}%)")
    print(f"❌ Невдалі запити: {failed} ({error_rate:.1f}%)")
    print(f"⏱️  Загальний час: {total_time:.2f} секунд")
    print(f"⚡ Throughput: {total_requests / total_time:.2f} req/s")

    # Статистика по операціях
    for op_name, op_results in by_operation.items():
        print(f"\n📌 Операція: {op_name}")
        print(f"   {'─' * 60}")

        successful_ops = [r for r in op_results if r['success']]
        failed_ops = [r for r in op_results if not r['success']]

        print(f"   Всього запитів: {len(op_results)}")
        print(f"   Успішно: {len(successful_ops)}")
        print(f"   Невдало: {len(failed_ops)}")

        if successful_ops:
            response_times = [r['response_time'] for r in successful_ops]
            print(f"\n   ⏱️  Час відгуку (успішні запити):")
            print(f"      Мінімальний: {min(response_times):.2f} ms")
            print(f"      Середній: {statistics.mean(response_times):.2f} ms")
            print(f"      Медіана: {statistics.median(response_times):.2f} ms")
            print(f"      Максимальний: {max(response_times):.2f} ms")

            if len(response_times) >= 20:
                percentiles = statistics.quantiles(response_times, n=100)
                print(f"      95th percentile: {percentiles[94]:.2f} ms")
                print(f"      99th percentile: {percentiles[98]:.2f} ms")

        # Аналіз помилок
        if failed_ops:
            error_types = {}
            for r in failed_ops:
                error = r.get('error', 'Unknown')
                error_types[error] = error_types.get(error, 0) + 1

            print(f"\n   ❌ Типи помилок:")
            for error_type, count in error_types.items():
                print(f"      {error_type}: {count} ({count / len(op_results) * 100:.1f}%)")

    print(f"\n{'=' * 70}\n")

    return {
        'total_requests': total_requests,
        'successful': successful,
        'failed': failed,
        'error_rate': error_rate,
        'total_time': total_time,
        'throughput': total_requests / total_time,
        'by_operation': by_operation
    }


async def main():
    if not check_db_exists():
        return

    print("=" * 70)
    print("🎯 ТЕСТУВАННЯ ПРОДУКТИВНОСТІ TELEGRAM БОТА")
    print("   (Симуляція навантаження на БД та логіку)")
    print("=" * 70)

    all_test_results = {}

    # Запускаємо тести з різним навантаженням
    for num_users in CONCURRENT_USERS:
        result = await run_load_test(num_users, REQUESTS_PER_USER)
        all_test_results[num_users] = result

        # Пауза між тестами
        await asyncio.sleep(2)

    print("\n" + "=" * 70)
    print("📈 ПІДСУМКОВИЙ ЗВІТ")
    print("=" * 70)
    print(f"\n{'Користувачів':<15} {'Throughput':<15} {'Error Rate':<15} {'Avg Response Time':<20}")
    print("─" * 70)

    for num_users, result in all_test_results.items():
        # Обчислюємо середній час відгуку
        all_response_times = []
        for op_results in result['by_operation'].values():
            for r in op_results:
                if r['success']:
                    all_response_times.append(r['response_time'])

        avg_response = statistics.mean(all_response_times) if all_response_times else 0

        print(f"{num_users:<15} {result['throughput']:<15.2f} "
              f"{result['error_rate']:<15.1f}% {avg_response:<20.2f} ms")

    print("\n" + "=" * 70)
    print("✅ Тестування завершено!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    asyncio.run(main())