import os
import sys
import unittest
import asyncio
from datetime import datetime, timezone

os.environ["PYTHONIOENCODING"] = "utf-8"

from database.session import db
from database.models.user import User, UserRole
from database.models.hotel import Hotel
from database.models.category import Category
from database.models.product import Product
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem

from database.repositories.user_repository import UserRepository
from database.repositories.hotel_repository import HotelRepository
from database.repositories.category_repository import CategoryRepository
from database.repositories.product_repository import ProductRepository
from database.repositories.order_repository import OrderRepository
from services.auth_service import AuthService
from services.order_service import OrderService
from utils.excel_export import generate_excel, generate_hotel_orders_excel


class TestFullSystemLifecycle(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session = db
        self.user_repo = UserRepository(self.session)
        self.hotel_repo = HotelRepository(self.session)
        self.cat_repo = CategoryRepository(self.session)
        self.prod_repo = ProductRepository(self.session)
        self.order_repo = OrderRepository(self.session)
        self.auth_service = AuthService(self.user_repo)
        self.order_service = OrderService(self.session)

        # Unique IDs for test isolation
        self.test_hotel_name = f"Lifecycle Grand Hotel {int(datetime.now().timestamp())}"
        self.hotel = None
        self.hotel_admin = None
        self.hotel_staff = None
        self.driver = None
        self.store_manager = None
        self.category = None
        self.product = None
        self.order = None

    async def asyncTearDown(self):
        # Cleanup all created test entities
        if self.order:
            await self.order_repo.delete(self.order)
        if self.product:
            await self.prod_repo.delete(self.product)
        if self.category:
            await self.cat_repo.delete(self.category)
        if self.hotel_staff:
            await self.user_repo.delete(self.hotel_staff)
        if self.hotel_admin:
            await self.user_repo.delete(self.hotel_admin)
        if self.driver:
            await self.user_repo.delete(self.driver)
        if self.store_manager:
            await self.user_repo.delete(self.store_manager)
        if self.hotel:
            await self.hotel_repo.delete(self.hotel)

    async def test_complete_business_lifecycle(self):
        # =========================================================================
        # 1. HOTEL CREATION & 1-TO-1 HOTEL ADMIN RELATIONSHIP
        # =========================================================================
        hotel = Hotel(
            name=self.test_hotel_name,
            address="Bole Medhanialem, Addis Ababa",
            phone="0911002233",
            is_active=True,
        )
        self.hotel = await self.hotel_repo.create(hotel)
        self.assertIsNotNone(self.hotel.id)

        # First user registering under hotel -> Becomes HOTEL_ADMIN (1-to-1)
        self.hotel_admin = await self.auth_service.register_user(
            telegram_id=90000001,
            full_name="Abel Hotel Admin",
            username="abel_admin",
            phone="0911111111",
            hotel_id=self.hotel.id,
            role="hotel_admin",
            is_active=True,
        )
        self.assertIsNotNone(self.hotel_admin.id)
        
        # Verify 1-to-1 hotel admin lookup
        verified_admin = await self.user_repo.get_hotel_admin(self.hotel.id)
        self.assertIsNotNone(verified_admin)
        self.assertEqual(verified_admin.id, self.hotel_admin.id)

        # Second user registering under SAME hotel -> Must be registered as CUSTOMER (staff)
        # This confirms 1-to-1 guarantee: Only one admin per hotel, others are ordering staff
        self.hotel_staff = await self.auth_service.register_user(
            telegram_id=90000002,
            full_name="Sara Staff",
            username="sara_staff",
            phone="0922222222",
            hotel_id=self.hotel.id,
            role="customer",
            is_active=True,
        )
        self.assertIsNotNone(self.hotel_staff.id)
        role_val = self.hotel_staff.role.value if hasattr(self.hotel_staff.role, "value") else str(self.hotel_staff.role)
        self.assertEqual(role_val, "customer")

        # =========================================================================
        # 2. DRIVER & STORE MANAGER REGISTRATION
        # =========================================================================
        self.driver = await self.auth_service.register_user(
            telegram_id=90000003,
            full_name="Kebede Driver",
            username="kebede_fast",
            phone="0933333333",
            hotel_id=None,
            role="driver",
            is_active=True,
        )
        self.assertIsNotNone(self.driver.id)

        self.store_manager = await self.auth_service.register_user(
            telegram_id=90000004,
            full_name="Almaz Store Manager",
            username="almaz_store",
            phone="0944444444",
            hotel_id=None,
            role="store_manager",
            is_active=True,
        )
        self.assertIsNotNone(self.store_manager.id)

        # Verify active drivers retrieval for assignment
        drivers = await self.user_repo.get_delivery_partners()
        self.assertTrue(any(d.id == self.driver.id for d in drivers))

        # =========================================================================
        # 3. CATALOG SETUP: CATEGORY & PRODUCT
        # =========================================================================
        self.category = await self.cat_repo.create(Category(name="Fresh Vegetables", is_active=True))
        self.product = await self.prod_repo.create(
            Product(
                category_id=self.category.id,
                name="Organic Red Onion",
                unit="KG",
                is_active=True,
            )
        )
        self.assertIsNotNone(self.product.id)

        # =========================================================================
        # 4. ORDER PLACEMENT FLOW (HOTEL STAFF / CUSTOMER)
        # =========================================================================
        items = [
            OrderItem(product_id=self.product.id, quantity=25.0)
        ]
        self.order = await self.order_service.create_order(
            customer_id=self.hotel_staff.id,
            hotel_id=self.hotel.id,
            items=items,
            note="Deliver to back kitchen door",
        )
        self.assertIsNotNone(self.order.id)
        self.assertTrue(self.order.order_number.startswith("OYR-"))
        self.assertEqual(self.order.status, OrderStatus.SUBMITTED)

        # =========================================================================
        # 5. STORE MANAGER / ADMIN ORDER REVIEW & PREPARATION FLOW
        # =========================================================================
        # Step A: Approve Order with driver name
        approved_order, status_code = await self.order_repo.approve_order(
            self.order.id,
            driver_name="Kebede Driver",
        )
        self.assertEqual(status_code, "ok")
        self.assertEqual(approved_order.status, OrderStatus.APPROVED.value)

        # Step B: Mark Preparing
        prep_order = await self.order_repo.update_order_status(
            self.order.id,
            OrderStatus.PREPARING,
        )
        self.assertEqual(prep_order.status, OrderStatus.PREPARING.value)

        # Step C: Mark Packed & Ready
        packed_order = await self.order_repo.update_order_status(
            self.order.id,
            OrderStatus.PACKED,
        )
        self.assertEqual(packed_order.status, OrderStatus.PACKED.value)

        # =========================================================================
        # 6. DRIVER ASSIGNMENT & DELIVERY EXECUTION FLOW
        # =========================================================================
        # Assign driver by ID
        assigned_order, assign_code = await self.order_repo.assign_driver(
            self.order.id,
            driver_id=self.driver.id,
        )
        self.assertEqual(assign_code, "ok")
        self.assertEqual(assigned_order.delivery_partner_id, self.driver.id)

        # Driver accepts / picks up (OUT_FOR_DELIVERY)
        out_order, accept_code = await self.order_repo.driver_accept(
            self.order.id,
            driver_id=self.driver.id,
        )
        self.assertEqual(accept_code, "ok")
        self.assertEqual(out_order.status, OrderStatus.OUT_FOR_DELIVERY.value)

        # Driver marks delivered (DELIVERED)
        delivered_order, complete_code = await self.order_repo.driver_complete(
            self.order.id,
            driver_id=self.driver.id,
        )
        self.assertEqual(complete_code, "ok")
        self.assertEqual(delivered_order.status, OrderStatus.DELIVERED.value)
        self.assertIsNotNone(delivered_order.delivered_at)

        # =========================================================================
        # 7. EXCEL REPORT GENERATION CHECK
        # =========================================================================
        full_excel = generate_excel([delivered_order], {})
        self.assertGreater(len(full_excel), 100)

        hotel_excel = generate_hotel_orders_excel(self.hotel, [delivered_order])
        self.assertGreater(len(hotel_excel), 100)


if __name__ == "__main__":
    unittest.main()
