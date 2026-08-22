import unittest
from datetime import datetime
from utils.helpers import generate_order_number
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem

class TestOrderService(unittest.TestCase):
    def test_generate_order_number(self):
        order_no = generate_order_number(42)
        self.assertTrue(order_no.startswith('OYR-'))
        self.assertTrue(order_no.endswith('-0042'))

    def test_order_status_transitions(self):
        order = Order(id=1, customer_id=10, hotel_id=5, status=OrderStatus.SUBMITTED)
        self.assertEqual(order.status, OrderStatus.SUBMITTED)
        
        order.status = OrderStatus.APPROVED
        self.assertEqual(order.status, OrderStatus.APPROVED)
        
        order.status = OrderStatus.OUT_FOR_DELIVERY
        order.driver_id = 99
        order.driver_name = 'Test Driver'
        self.assertEqual(order.driver_name, 'Test Driver')

        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.utcnow()
        self.assertIsNotNone(order.delivered_at)

    def test_order_item_associations(self):
        item = OrderItem(id=1, order_id=100, product_id=50, quantity=12.5)
        d = item.to_dict()
        self.assertEqual(d['product_id'], 50)
        self.assertEqual(d['quantity'], 12.5)

if __name__ == '__main__':
    unittest.main()
