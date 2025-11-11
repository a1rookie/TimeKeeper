import requests
BASE_URL = 'http://localhost:8000'
print('--- TimeKeeper E2E Test ---')
r = requests.post(f'{BASE_URL}/api/v1/users/login', json={'phone': '13800138000', 'password': 'test123'})
token = r.json()['access_token']
print(f'[OK] Login: {r.status_code}')
h = {'Authorization': f'Bearer {token}'}
r = requests.get(f'{BASE_URL}/api/v1/users/me', headers=h)
print(f'[OK] Get User: {r.status_code}')
data = {'title': 'Test', 'description': 'Test', 'category': 'health', 'recurrence_type': 'daily', 'recurrence_config': {'interval': 1}, 'first_remind_time': '2025-02-01T09:00:00', 'remind_channels': ['app'], 'advance_minutes': 0}
r = requests.post(f'{BASE_URL}/api/v1/reminders/', json=data, headers=h)
print(f'[OK] Create Reminder: {r.status_code}')
rid = r.json()['id']
r = requests.get(f'{BASE_URL}/api/v1/reminders/', headers=h)
print(f'[OK] List Reminders: {r.status_code}, Count: {len(r.json())}')
r = requests.put(f'{BASE_URL}/api/v1/reminders/{rid}', json={'title': 'Updated'}, headers=h)
print(f'[OK] Update Reminder: {r.status_code}')
r = requests.delete(f'{BASE_URL}/api/v1/reminders/{rid}', headers=h)
print(f'[OK] Delete Reminder: {r.status_code}')
print('[SUCCESS] All tests passed!')
