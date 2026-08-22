import unittest
from datetime import datetime
from database.models.user import User, UserRole
from database.models.hotel import Hotel
from database.models.category import Category
from database.models.product import Product
from database.models.order import Order, OrderStatus

class TestModels(unittest.TestCase):
    def test_user_model(self):
        user = User(
            id=1,
            telegram_id=123456789,
            full_name='Test User',
            role=UserRole.CUSTOMER,
            language='om',
            is_active=True
        )
        d = user.to_dict()
        self.assertEqual(d['telegram_id'], 123456789)
        self.assertEqual(d['language'], 'om')
        self.assertEqual(d['role'], 'customer')

        reconstructed = User.from_dict(d)
        self.assertEqual(reconstructed.id, 1)
        self.assertEqual(reconstructed.language, 'om')
        self.assertEqual(reconstructed.role, UserRole.CUSTOMER)

    def test_hotel_model(self):
        hotel = Hotel(id=10, name='Grand Hotel', address='Bole, Addis Ababa', is_active=True)
        d = hotel.to_dict()
        self.assertEqual(d['name'], 'Grand Hotel')
        reconstructed = Hotel.from_dict(d)
        self.assertEqual(reconstructed.name, 'Grand Hotel')

    def test_category_and_product(self):
        cat = Category(id=5, name='Vegetables', is_active=True)
        prod = Product(id=20, name='Tomatoes', category_id=5, unit='KG', is_active=True)
        self.assertEqual(cat.to_dict()['name'], 'Vegetables')
        self.assertEqual(prod.to_dict()['unit'], 'KG')

    def test_order_model(self):
        order = Order(
            id=100,
            order_number='ORD-2026-001',
            customer_id=1,
            hotel_id=10,
            status=OrderStatus.SUBMITTED,
            note='Urgent delivery'
        )
        d = order.to_dict()
        self.assertEqual(d['order_number'], 'ORD-2026-001')
        self.assertEqual(d['status'], 'Submitted')
        reconstructed = Order.from_dict(d)
        self.assertEqual(reconstructed.order_number, 'ORD-2026-001')

if __name__ == '__main__':
    unittest.main()
