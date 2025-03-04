# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import DataValidationError, Product, Category, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_update_a_product(self):
        """It should update a product name"""
        products = Product.all()
        self.assertEqual(products, [])
        base_product = ProductFactory()
        base_product.id = None
        base_product.create()
        base_product.name = "Ferrari"
        base_product.update()
        products = Product.all()
        updated_product = products[0]
        self.assertEqual(updated_product.name, "Ferrari")

    def test_update_a_product_without_id(self):
        """It should raise a data validation error if updated product doesn't have an ID"""
        products = Product.all()
        self.assertEqual(products, [])
        base_product = ProductFactory()
        base_product.id = None
        base_product.create()
        base_product.id = None
        self.assertRaises(DataValidationError, base_product.update)

    def test_deleting_a_product(self):
        """It should delete a product in the stock"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        products = Product.all()
        self.assertEqual(len(products), 1)
        product.delete()
        products = Product.all()
        self.assertEqual(products, [])

    def test_deserializing_invalid_available_product(self):
        """It should raise a DataValidationError if product available field is not a boolean"""
        product = ProductFactory()
        product_dict = product.serialize()
        product_dict["available"] = "asdf"
        self.assertRaises(DataValidationError, product.deserialize, product_dict)
       
    def test_invalid_product_category(self):
        """It should raise an DataValidationError if received an invalid Category"""
        product = ProductFactory()
        product_dict = product.serialize()
        product_dict["category"] = "asdf"
        self.assertRaises(DataValidationError, product.deserialize, product_dict)

    def test_invalid_product_category_data_type(self):
        """It should raise an DataValidationError if received a number as Category"""
        product = ProductFactory()
        product_dict = product.serialize()
        product_dict["category"] = 69
        self.assertRaises(DataValidationError, product.deserialize, product_dict)

    def test_find_a_product(self):
        """It should return a product by its ID"""
        product = ProductFactory()
        product.id = None
        product.create()
        products = Product.all()
        db_product = Product.find(products[0].id)
        self.assertEqual(products[0], db_product)

    def test_find_product_by_name(self):
        """It should return only the product with an exact name match"""
        product_names = ["p1", "p2", "p3", "p1"]
        for product_name in product_names:
            product = ProductFactory()
            product.name = product_name
            product.id = None
            product.create()
        products_p1s = Product.find_by_name("p1")
        self.assertEqual(len(products_p1s), 2)

    def test_find_product_by_price(self):
        """It should return a product with the exatct price"""
        for _ in range(5):
            product = ProductFactory()
            product.id = None
            product.create()
        products = Product.all()
        last_product_price = products[-1].price
        product_by_price = Product.find_by_price(last_product_price)
        self.assertEqual(product_by_price[0], products[-1])

    def test_find_product_by_price_as_str(self):
        """It should convert a price str to Decimal and return the product with the provided price"""
        for _ in range(5):
            product = ProductFactory()
            product.id = None
            product.create()
        products = Product.all()
        last_product_price = products[-1].price
        str_price = f'"{last_product_price}"'
        product_by_price = Product.find_by_price(str_price)
        self.assertEqual(product_by_price[0], products[-1])

    def test_find_available_products(self):
        """It should return only available product"""
        for idx in range(5):
            product = ProductFactory()
            product.id = None
            product.available = idx % 2 == 0
            product.create()
        available_products = Product.find_by_availability(True)
        self.assertEqual(len(available_products), 3)

    def test_find_products_by_category(self):
        """It should return products from a given category"""
        for category in [Category.AUTOMOTIVE, Category.HOUSEWARES, Category.AUTOMOTIVE]:
            product = ProductFactory()
            product.id = None
            product.category = category
            product.create()
        products = Product.find_by_category(Category.AUTOMOTIVE)
        self.assertEqual(len(products), 2)
