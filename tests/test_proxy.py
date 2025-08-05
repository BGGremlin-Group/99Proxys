#!/usr/bin/env python3
"""
Test Suite
To ensure the code is production-ready, 
We've included a unittest-based test suite
In a separate file (tests/test_proxy.py).
This should be placed in a tests/ directory within the project.python
# tests/test_proxy.py
"""
import unittest
import os
import shutil
from pathlib import Path
from main import ProxyNode, ProxyChain, Website, Page, Review, ChatMessage, db, flask_app, SITES_DIR

class TestProxyChain(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.chain = ProxyChain()
        self.chain.config["node_count"] = 1
        self.test_website = "test_website"
        self.test_page = {
            "name": "index",
            "html_content": "<html><body>Test</body></html>",
            "css_content": "body { color: black; }",
            "js_content": "console.log('Test');"
        }
        self.test_dir = SITES_DIR / self.test_website
        with flask_app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test environment."""
        self.chain.stop()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        with flask_app.app_context():
            db.drop_all()

    def test_node_initialization(self):
        """Test proxy node initialization."""
        self.chain.initialize_nodes()
        self.assertEqual(len(self.chain.nodes), 1)
        self.assertTrue(self.chain.nodes[0].active)
        self.assertEqual(self.chain.nodes[0].host, "127.0.0.1")
        self.assertTrue(self.chain.nodes[0].port in self.chain.used_ports)

    def test_website_creation(self):
        """Test website creation."""
        self.chain.create_website(self.test_website, [self.test_page])
        self.assertTrue(self.test_dir.exists())
        self.assertTrue((self.test_dir / "index" / "index.html").exists())
        with flask_app.app_context():
            website = Website.query.filter_by(name=self.test_website).first()
            self.assertIsNotNone(website)
            page = Page.query.filter_by(website_id=website.id, name="index").first()
            self.assertIsNotNone(page)
            self.assertEqual(page.html_content, self.test_page["html_content"])

    def test_review_submission(self):
        """Test review submission."""
        self.chain.create_website(self.test_website, [self.test_page])
        with flask_app.app_context():
            website = Website.query.filter_by(name=self.test_website).first()
            review = Review(
                website_id=website.id,
                name="Test User",
                rating=5,
                comment="Great website!",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            db.session.add(review)
            db.session.commit()
            reviews = Review.query.filter_by(website_id=website.id).all()
            self.assertEqual(len(reviews), 1)
            self.assertEqual(reviews[0].rating, 5)

    def test_chat_message(self):
        """Test chat message handling."""
        self.chain.create_website(self.test_website, [self.test_page])
        with flask_app.app_context():
            website = Website.query.filter_by(name=self.test_website).first()
            msg = ChatMessage(
                website_id=website.id,
                username="TestUser",
                message="Hello, world!",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            db.session.add(msg)
            db.session.commit()
            messages = ChatMessage.query.filter_by(website_id=website.id).all()
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0].message, "Hello, world!")

    def test_virtual_ip_assignment(self):
        """Test virtual IP assignment."""
        self.chain.initialize_nodes()
        node = self.chain.nodes[0]
        self.assertTrue(node.virtual_ip in self.chain.used_ips)
        network = ipaddress.IPv4Network(node.locale["ip_prefix"], strict=False)
        self.assertTrue(ipaddress.IPv4Address(node.virtual_ip) in network)

    def test_bandwidth_throttling(self):
        """Test bandwidth throttling."""
        self.chain.initialize_nodes()
        node = self.chain.nodes[0]
        node.bandwidth_limit_kbps = 100  # 100 kbps
        initial_tokens = node.bucket_tokens
        node.throttle_bandwidth(10000)  # 10KB
        self.assertLess(node.bucket_tokens, initial_tokens)

if __name__ == '__main__':
    unittest.main()
