import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Метрика для відстеження помилок
const errorRate = new Rate('errors');

// Конфігурація навантаження
export const options = {
  stages: [
    { duration: '1m', target: 10 },   // За 1 хв підняти до 10 користувачів
    { duration: '2m', target: 10 },   // 2 хв тримати 10 користувачів
    { duration: '1m', target: 50 },   // За 1 хв підняти до 50
    { duration: '3m', target: 50 },   // 3 хв тримати 50
    { duration: '1m', target: 0 },    // За 1 хв зменшити до 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% запитів мають бути швидше 2 сек
    errors: ['rate<0.1'],              // Помилок має бути менше 10%
  },
};


const BOT_TOKEN = '8593640683:AAFYUu1sIgebbneJfSf9cbCbejDUoWSvNv8';
const API_BASE = `https://api.telegram.org/bot${BOT_TOKEN}`;

// Тестові користувачі
const users = [
  { chat_id: 101, username: 'admin_alex', role: 'admin' },
  { chat_id: 201, username: 'user_ivan', role: 'student' },
  { chat_id: 301, username: 'teacher_olga', role: 'teacher' },
  { chat_id: 401, username: 'student_petro', role: 'student' },
  { chat_id: 501, username: 'guest_user', role: 'student' },
];

export default function () {
  // Вибираємо випадкового користувача
  const user = users[Math.floor(Math.random() * users.length)];

  // Сценарій 1: Команда /start
  let startResponse = http.post(`${API_BASE}/sendMessage`, JSON.stringify({
    chat_id: user.chat_id,
    text: '/start',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  let startSuccess = check(startResponse, {
    '/start: status 200': (r) => r.status === 200,
    '/start: telegram ok': (r) => r.json('ok') === true,
  });

  if (!startSuccess) {
    errorRate.add(1);
    console.log(`❌ /start failed for user ${user.chat_id}: ${startResponse.status}`);
  }

  // Імітація часу читання відповіді
  sleep(Math.random() * 2 + 1); // 1-3 секунди

  // Сценарій 2: Створення групи (лише для teachers/admins)
  if (user.role === 'teacher' || user.role === 'admin') {
    const groupName = `Group_${Date.now()}_${Math.floor(Math.random() * 1000)}`;

    let groupResponse = http.post(`${API_BASE}/sendMessage`, JSON.stringify({
      chat_id: user.chat_id,
      text: `/create_group ${groupName}`,
    }), {
      headers: { 'Content-Type': 'application/json' },
    });

    let groupSuccess = check(groupResponse, {
      'create_group: status 200': (r) => r.status === 200,
    });

    if (!groupSuccess) {
      errorRate.add(1);
      console.log(`❌ create_group failed for ${user.username}`);
    }

    sleep(Math.random() * 2 + 2); // 2-4 секунди

    // Сценарій 3: Створення конференції (FSM - 4 кроки)

    // Початок створення
    let confStartResponse = http.post(`${API_BASE}/sendMessage`, JSON.stringify({
      chat_id: user.chat_id,
      text: '/create_conference',
    }), {
      headers: { 'Content-Type': 'application/json' },
    });

    check(confStartResponse, {
      'conference_start: status 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    sleep(2); // Користувач думає над назвою

    // Введення назви
    let confNameResponse = http.post(`${API_BASE}/sendMessage`, JSON.stringify({
      chat_id: user.chat_id,
      text: `Тестова конференція ${Date.now()}`,
    }), {
      headers: { 'Content-Type': 'application/json' },
    });

    check(confNameResponse, {
      'conference_name: status 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    sleep(2); // Користувач вводить дату

    // Введення дати
    let confDateResponse = http.post(`${API_BASE}/sendMessage`, JSON.stringify({
      chat_id: user.chat_id,
      text: '25.12.2025 14:00',
    }), {
      headers: { 'Content-Type': 'application/json' },
    });

    check(confDateResponse, {
      'conference_date: status 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    sleep(1.5); // Користувач копіює посилання

    // Введення посилання
    let confLinkResponse = http.post(`${API_BASE}/sendMessage`, JSON.stringify({
      chat_id: user.chat_id,
      text: `https://zoom.us/j/${Math.floor(Math.random() * 900000) + 100000}`,
    }), {
      headers: { 'Content-Type': 'application/json' },
    });

    let confSuccess = check(confLinkResponse, {
      'conference_link: status 200': (r) => r.status === 200,
    });

    if (!confSuccess) {
      errorRate.add(1);
      console.log(`❌ conference creation failed for ${user.username}`);
    }
  }

  // Пауза перед наступною ітерацією
  sleep(Math.random() * 3 + 2); // 2-5 секунд
}

// Обробка результатів після завершення тесту
export function handleSummary(data) {
  console.log('\n' + '='.repeat(60));
  console.log(' ПІДСУМОК ТЕСТУВАННЯ ПРОДУКТИВНОСТІ');
  console.log('='.repeat(60));

  const httpReqs = data.metrics.http_reqs.values;
  const httpDuration = data.metrics.http_req_duration.values;
  const errors = data.metrics.errors.values;

  console.log(`\n Загальна кількість запитів: ${httpReqs.count}`);
  console.log(` Показник помилок: ${(errors.rate * 100).toFixed(2)}%`);
  console.log(` Пропускна здатність: ${httpReqs.rate.toFixed(2)} req/s`);

  console.log(`\n⏱️  ЧАС ВІДГУКУ:`);
  console.log(`   Мінімальний: ${httpDuration.min.toFixed(2)} ms`);
  console.log(`   Середній: ${httpDuration.avg.toFixed(2)} ms`);
  console.log(`   Медіана: ${httpDuration.med.toFixed(2)} ms`);
  console.log(`   95th percentile: ${httpDuration['p(95)'].toFixed(2)} ms`);
  console.log(`   99th percentile: ${httpDuration['p(99)'].toFixed(2)} ms`);
  console.log(`   Максимальний: ${httpDuration.max.toFixed(2)} ms`);

  console.log('\n' + '='.repeat(60) + '\n');

  return {
    'stdout': '',
  };
}