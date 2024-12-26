import unittest
from app import app  # Претпоставуваме дека Flask апликацијата е во app.py
import json

class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        """Ова ќе се изврши пред секој тест, инициализирање на тест серверот."""
        self.app = app.test_client()
        self.app.testing = True

    def test_get_all_users(self):
        """Тест за /users ендпоинт"""
        response = self.app.get('/users')
        self.assertEqual(response.status_code, 200)
        # Проверка дали JSON е вратен
        self.assertIsInstance(response.json, list)

    def test_get_total_spent(self):
        """Тест за /total_spent/<user_id> ендпоинт"""
        user_id = 1  # Ова е пример, проверете дали корисникот постои во вашата база
        response = self.app.get(f'/total_spent/{user_id}')
        self.assertEqual(response.status_code, 200)
        # Проверка дали се враќа точниот износ за потрошени пари
        self.assertIn('total_spent', response.json)

    def test_get_high_spenders(self):
        """Тест за /high_spenders ендпоинт"""
        response = self.app.get('/high_spenders')
        self.assertEqual(response.status_code, 200)
        # Проверка дали резултатот е листа
        self.assertIsInstance(response.json, list)

    def test_average_spending_by_age(self):
        """Тест за /average_spending_by_age ендпоинт"""
        response = self.app.get('/average_spending_by_age')
        self.assertEqual(response.status_code, 200)
        # Проверка дали резултатот е речник со возрастни групи
        self.assertIsInstance(response.json, dict)

    def test_write_high_spending_user_valid(self):
        """Тест за /write_high_spending_user со валидни податоци"""
        data = {
            'user_id': 1,
            'total_spending': 1500
        }
        response = self.app.post('/write_high_spending_user', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json)

    def test_write_high_spending_user_invalid_data(self):
        """Тест за /write_high_spending_user со невалидни податоци"""
        data = {
            'user_id': 1,
            'total_spending': 500  # Ова не е доволно, треба да е >= 1000
        }
        response = self.app.post('/write_high_spending_user', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_write_high_spending_user_missing_fields(self):
        """Тест за /write_high_spending_user со недоволни податоци"""
        data = {
            'user_id': 1
        }  # Недостасува 'total_spending'
        response = self.app.post('/write_high_spending_user', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_get_total_spent_user_not_found(self):
        """Тест за /total_spent/<user_id> кога корисникот не постои"""
        user_id = 99999  # Корисник кој не постои
        response = self.app.get(f'/total_spent/{user_id}')
        self.assertEqual(response.status_code, 200)
        # Очекиваме дека нема потрошени пари
        self.assertEqual(response.json['total_spent'], 0)


if __name__ == '__main__':
    unittest.main()
