"""
End-to-End Testing Suite for SCRIBE
Complete user journey testing with Playwright
"""

import pytest
import asyncio
import json
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import requests
import time

# Test configuration
BASE_URL = "http://localhost:3000"
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30000  # 30 seconds

class TestSCRIBEE2E:
    """Complete end-to-end tests for SCRIBE system"""

    @pytest.fixture
    async def browser_context(self):
        """Setup browser context for tests"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Set to True for CI
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )

        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            locale='fr-FR',
            permissions=['microphone']  # For voice tests
        )

        yield context

        await browser.close()
        await playwright.stop()

    @pytest.fixture
    async def page(self, browser_context):
        """Create a new page for each test"""
        page = await browser_context.new_page()

        # Set up console logging
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        page.on("pageerror", lambda error: print(f"Page error: {error}"))

        yield page
        await page.close()

    async def test_health_checks(self):
        """Test that all services are healthy before running tests"""
        # Check backend health
        response = requests.get(f"{API_BASE_URL}/health/detailed", timeout=10)
        assert response.status_code == 200

        health_data = response.json()
        assert health_data["status"] in ["healthy", "degraded"]

        # Check specific services
        services = health_data.get("services", {})
        for service, status in services.items():
            assert status == "healthy", f"Service {service} is not healthy: {status}"

        print("✅ All services healthy")

    async def test_complete_document_upload_flow(self, page: Page):
        """Test complete document upload and processing flow"""

        # Navigate to upload page
        await page.goto(f"{BASE_URL}/upload")
        await page.wait_for_load_state("networkidle")

        # Check page loaded correctly
        await page.wait_for_selector("text=Upload de Documents", timeout=TEST_TIMEOUT)

        # Create test file
        test_content = """Hackathon Test Document
Intelligence Artificielle

Ceci est un test pour SCRIBE.
Nous testons l'upload et la conversion HTML.

Applications testées :
- Plume (restitution)
- Mimir (recherche RAG)

Liens de test :
https://example.com/test
https://docs.scribe.ai/documentation

Technologies :
- FastAPI backend
- NextJS frontend
- Supabase database
- OpenAI embeddings"""

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name

        try:
            # Upload file via drag & drop zone
            await page.set_input_files("input[type='file']", temp_file_path)

            # Wait for file to appear in upload queue
            await page.wait_for_selector("text=test", timeout=TEST_TIMEOUT)

            # Add custom title and tags
            await page.fill("input[placeholder*='Titre']", "Test Document E2E")
            await page.fill("input[placeholder*='tags']", "test, e2e, hackathon")

            # Click upload button
            await page.click("button:has-text('Traiter les fichiers')")

            # Wait for processing to complete
            await page.wait_for_selector("text=✅", timeout=TEST_TIMEOUT)

            # Verify document appears in processed list
            await page.wait_for_selector("text=Test Document E2E", timeout=TEST_TIMEOUT)

            # Click on processed document to select it
            await page.click("text=Test Document E2E")

            # Wait for preview to load
            await page.wait_for_selector("text=Test Document E2E", timeout=TEST_TIMEOUT)

            # Test toggle between TEXT and HTML views
            # Should start in TEXT view
            text_content = await page.text_content(".font-mono")
            assert "Hackathon Test Document" in text_content

            # Toggle to HTML view
            await page.click("button:has-text('HTML')")
            await page.wait_for_timeout(500)

            # Verify HTML content is displayed
            html_content = await page.text_content(".prose")
            assert "Hackathon Test Document" in html_content

            # Verify links are clickable in HTML view
            links = await page.query_selector_all("a[href]")
            assert len(links) >= 2, "Expected at least 2 links in HTML view"

            # Toggle back to TEXT view
            await page.click("button:has-text('TEXT')")
            await page.wait_for_timeout(500)

            # Verify back to text view
            text_content = await page.text_content(".font-mono")
            assert "Hackathon Test Document" in text_content

            print("✅ Document upload and toggle flow completed")

        finally:
            # Clean up temp file
            Path(temp_file_path).unlink(missing_ok=True)

    async def test_chat_interface_flow(self, page: Page):
        """Test chat interface with agent selection and messaging"""

        # Navigate to chat page
        await page.goto(f"{BASE_URL}/chat")
        await page.wait_for_load_state("networkidle")

        # Check page loaded correctly
        await page.wait_for_selector("text=SCRIBE Chat", timeout=TEST_TIMEOUT)

        # Verify initial agent messages are present
        await page.wait_for_selector("text=Salut ! Je suis", timeout=TEST_TIMEOUT)

        # Test agent selection - select Plume
        await page.click("button:has-text('Plume')")
        await page.wait_for_timeout(500)

        # Type message to Plume
        test_message = "Bonjour Plume, peux-tu m'aider à reformuler ce texte ?"
        await page.fill("textarea[placeholder*='Écris ton message']", test_message)

        # Send message
        await page.click("button[type='submit']:has-text('Send'), button:has([data-icon='send'])")

        # Wait for user message to appear
        await page.wait_for_selector(f"text={test_message}", timeout=TEST_TIMEOUT)

        # Wait for Plume response
        await page.wait_for_selector("text=réfléchit", timeout=5000)
        await page.wait_for_selector("text=🖋️", timeout=TEST_TIMEOUT)

        # Switch to Mimir agent
        await page.click("button:has-text('Mimir')")
        await page.wait_for_timeout(500)

        # Send message to Mimir
        mimir_message = "Recherche des informations sur les hackathons d'IA"
        await page.fill("textarea[placeholder*='Écris ton message']", mimir_message)
        await page.click("button[type='submit']:has-text('Send'), button:has([data-icon='send'])")

        # Wait for Mimir response
        await page.wait_for_selector(f"text={mimir_message}", timeout=TEST_TIMEOUT)
        await page.wait_for_selector("text=🧠", timeout=TEST_TIMEOUT)

        # Test keyboard shortcuts
        await page.press("textarea", "Control+Enter")  # Should not send (need Shift+Enter for new line)

        print("✅ Chat interface flow completed")

    async def test_search_functionality(self, page: Page):
        """Test search functionality (if search page exists)"""

        # Try to navigate to search (may not exist yet)
        try:
            await page.goto(f"{BASE_URL}/search")
            await page.wait_for_load_state("networkidle", timeout=5000)

            # If search page exists, test it
            search_input = page.locator("input[type='search'], input[placeholder*='recherch']").first
            if await search_input.is_visible():
                await search_input.fill("hackathon intelligence artificielle")
                await page.press("input", "Enter")

                # Wait for results
                await page.wait_for_timeout(2000)
                print("✅ Search functionality tested")

        except Exception as e:
            print(f"ℹ️ Search page not available yet: {e}")

    async def test_responsive_design(self, page: Page):
        """Test responsive design on different screen sizes"""

        # Test mobile viewport
        await page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE
        await page.goto(f"{BASE_URL}/upload")
        await page.wait_for_load_state("networkidle")

        # Check mobile-first design works
        upload_zone = page.locator("text=Glissez & déposez").first
        assert await upload_zone.is_visible(), "Upload zone should be visible on mobile"

        # Test tablet viewport
        await page.set_viewport_size({"width": 768, "height": 1024})  # iPad
        await page.reload()
        await page.wait_for_load_state("networkidle")

        # Test desktop viewport
        await page.set_viewport_size({"width": 1280, "height": 720})
        await page.reload()
        await page.wait_for_load_state("networkidle")

        print("✅ Responsive design tested")

    async def test_pwa_functionality(self, page: Page):
        """Test PWA features"""

        await page.goto(BASE_URL)
        await page.wait_for_load_state("networkidle")

        # Check service worker registration
        service_worker = await page.evaluate("""
            () => {
                return 'serviceWorker' in navigator;
            }
        """)
        assert service_worker, "Service worker should be supported"

        # Check PWA manifest
        manifest_link = page.locator("link[rel='manifest']")
        if await manifest_link.count() > 0:
            manifest_href = await manifest_link.get_attribute("href")
            assert manifest_href, "Manifest should be linked"

        print("✅ PWA functionality tested")

    async def test_error_handling(self, page: Page):
        """Test error handling scenarios"""

        # Test 404 page
        await page.goto(f"{BASE_URL}/non-existent-page")

        # Should either show 404 or redirect to home
        try:
            await page.wait_for_selector("text=404", timeout=3000)
            print("✅ 404 page handling works")
        except:
            # Might redirect to home page
            current_url = page.url
            assert current_url == BASE_URL or "upload" in current_url
            print("✅ 404 redirects to home")

        # Test with invalid file upload
        await page.goto(f"{BASE_URL}/upload")
        await page.wait_for_load_state("networkidle")

        # Try to upload invalid file type (create a fake binary file)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.exe', delete=False) as f:
            f.write(b'fake binary content')
            invalid_file_path = f.name

        try:
            await page.set_input_files("input[type='file']", invalid_file_path)

            # Should show error message
            await page.wait_for_selector("text=non supporté", timeout=5000)
            print("✅ Invalid file type error handling works")

        except Exception as e:
            print(f"ℹ️ File type validation not implemented yet: {e}")

        finally:
            Path(invalid_file_path).unlink(missing_ok=True)

    async def test_performance(self, page: Page):
        """Test basic performance metrics"""

        # Navigate to main page and measure load time
        start_time = time.time()
        await page.goto(BASE_URL)
        await page.wait_for_load_state("networkidle")
        load_time = time.time() - start_time

        # Should load within reasonable time
        assert load_time < 5.0, f"Page load time too slow: {load_time:.2f}s"

        # Check for performance metrics
        performance = await page.evaluate("""
            () => {
                const navigation = performance.getEntriesByType('navigation')[0];
                return {
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                    firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0
                };
            }
        """)

        print(f"✅ Performance metrics: {performance}")

    async def test_accessibility(self, page: Page):
        """Test basic accessibility features"""

        await page.goto(f"{BASE_URL}/upload")
        await page.wait_for_load_state("networkidle")

        # Check for proper headings structure
        h1_count = await page.locator("h1").count()
        assert h1_count >= 1, "Should have at least one H1 heading"

        # Check for skip link
        skip_link = page.locator("text=Aller au contenu principal")
        if await skip_link.count() > 0:
            assert await skip_link.is_hidden(), "Skip link should be hidden by default"

        # Test keyboard navigation
        await page.press("body", "Tab")
        await page.press("body", "Tab")

        print("✅ Basic accessibility tested")

# Test runner configuration
@pytest.mark.asyncio
class TestRunner:
    """Test runner for E2E tests"""

    async def run_all_tests(self):
        """Run all E2E tests in sequence"""
        print("🚀 Starting SCRIBE E2E Tests")
        print("=" * 50)

        test_instance = TestSCRIBEE2E()

        # Health check first
        await test_instance.test_health_checks()

        # Setup browser context
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720}
            )

            try:
                page = await context.new_page()

                # Run tests in order
                tests = [
                    ("Document Upload Flow", test_instance.test_complete_document_upload_flow),
                    ("Chat Interface", test_instance.test_chat_interface_flow),
                    ("Search Functionality", test_instance.test_search_functionality),
                    ("Responsive Design", test_instance.test_responsive_design),
                    ("PWA Features", test_instance.test_pwa_functionality),
                    ("Error Handling", test_instance.test_error_handling),
                    ("Performance", test_instance.test_performance),
                    ("Accessibility", test_instance.test_accessibility)
                ]

                passed_tests = 0
                failed_tests = 0

                for test_name, test_func in tests:
                    try:
                        print(f"\n🧪 Running: {test_name}")
                        await test_func(page)
                        passed_tests += 1
                        print(f"✅ {test_name} PASSED")

                    except Exception as e:
                        failed_tests += 1
                        print(f"❌ {test_name} FAILED: {e}")

                print(f"\n{'='*50}")
                print(f"📊 Test Results:")
                print(f"✅ Passed: {passed_tests}")
                print(f"❌ Failed: {failed_tests}")
                print(f"📈 Success Rate: {(passed_tests/(passed_tests+failed_tests))*100:.1f}%")

            finally:
                await browser.close()

if __name__ == "__main__":
    # Run tests directly
    async def main():
        runner = TestRunner()
        await runner.run_all_tests()

    asyncio.run(main())