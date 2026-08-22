import unittest
from datetime import datetime
from database.models.order import Order, OrderStatus
from database.models.hotel import Hotel
from utils.excel_export import generate_excel, generate_customer_excel, generate_driver_excel
from database.models.user import User

class TestExcelExport(unittest.TestCase):
    def test_generate_excel_empty(self):
        result = generate_excel([], {})
        self.assertIsInstance(result, bytes)
        self.assertTrue(len(result) > 0)

    def test_generate_excel_with_orders(self):
        hotel = Hotel(id=1, name='Test Hotel')
        order = Order(
            id=10,
            order_number='ORD-999',
            hotel=hotel,
            hotel_id=1,
            status=OrderStatus.DELIVERED,
            created_at=datetime.utcnow(),
            items=[]
        )
        stats = {
            'total_orders': 1,
            'delivered': 1,
            'pending': 0,
            'top_products': [('Onions', 50.0)]
        }
        result = generate_excel([order], stats)
        self.assertIsInstance(result, bytes)
        self.assertTrue(len(result) > 100)

    def test_generate_customer_excel(self):
        customer = User(id=1, full_name="Abebe Bikila", language="am")
        order = Order(
            id=10,
            order_number='ORD-101',
            customer=customer,
            status=OrderStatus.APPROVED,
            items=[]
        )
        result = generate_customer_excel(customer, [order])
        self.assertIsInstance(result, bytes)
        self.assertTrue(len(result) > 100)

    def test_generate_driver_excel(self):
        driver = User(id=2, full_name="Kebede Driver", language="om")
        order = Order(
            id=20,
            order_number='ORD-202',
            driver_name="Kebede Driver",
            status=OrderStatus.OUT_FOR_DELIVERY,
            items=[]
        )
        result = generate_driver_excel(driver, [order])
        self.assertIsInstance(result, bytes)
        self.assertTrue(len(result) > 100)

if __name__ == '__main__':
    unittest.main()

