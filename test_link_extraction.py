#!/usr/bin/env python3
"""
Playwright test script to debug the link extraction functionality
"""

import asyncio
import json
from playwright.async_api import async_playwright
import time

async def test_link_extraction():
    async with async_playwright() as p:
        # Launch browser with dev tools
        browser = await p.chromium.launch(
            headless=False,  # Show browser for debugging
            devtools=True    # Open dev tools
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging
        console_logs = []
        network_logs = []
        
        def handle_console(msg):
            console_logs.append({
                'type': msg.type,
                'text': msg.text,
                'location': msg.location
            })
            print(f"CONSOLE [{msg.type}]: {msg.text}")
        
        def handle_request(request):
            network_logs.append({
                'type': 'request',
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers)
            })
            print(f"REQUEST: {request.method} {request.url}")
        
        def handle_response(response):
            network_logs.append({
                'type': 'response',
                'url': response.url,
                'status': response.status,
                'headers': dict(response.headers)
            })
            print(f"RESPONSE: {response.status} {response.url}")
        
        page.on('console', handle_console)
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        try:
            print("1. Navigating to http://127.0.0.1:5000")
            await page.goto('http://127.0.0.1:5000', wait_until='networkidle')
            
            # Take initial screenshot
            await page.screenshot(path='C:/Users/Ryan.김준형/Documents/Projects/music_merger_project/initial_page.png')
            print("   - Initial screenshot saved")
            
            # Wait for page to load completely
            await page.wait_for_load_state('networkidle')
            
            print("2. Looking for link input field")
            # Find the link input field
            link_input = await page.wait_for_selector('input[type="url"], input[placeholder*="링크"], input[name="url"], #url-input', timeout=5000)
            print("   - Link input field found")
            
            print("3. Entering YouTube URL")
            await link_input.fill('https://www.youtube.com/watch?v=RUKqwwyAiEU')
            print("   - URL entered successfully")
            
            # Take screenshot after entering URL
            await page.screenshot(path='C:/Users/Ryan.김준형/Documents/Projects/music_merger_project/after_url_input.png')
            
            print("4. Looking for extract button")
            # Find and click the extract button
            extract_button = await page.wait_for_selector('button:has-text("🎵 추출"), button:has-text("추출"), input[type="submit"]', timeout=5000)
            print("   - Extract button found")
            
            # Take screenshot before clicking
            await page.screenshot(path='C:/Users/Ryan.김준형/Documents/Projects/music_merger_project/before_click.png')
            
            print("5. Clicking extract button")
            await extract_button.click()
            print("   - Extract button clicked")
            
            # Wait a moment for any immediate responses
            await page.wait_for_timeout(2000)
            
            print("6. Checking for progress indicators")
            # Look for progress indicators
            try:
                progress_element = await page.wait_for_selector('.progress, #progress, .loading, .spinner', timeout=3000)
                print("   - Progress indicator found")
                await page.screenshot(path='C:/Users/Ryan.김준형/Documents/Projects/music_merger_project/progress_shown.png')
            except:
                print("   - No progress indicator found within 3 seconds")
            
            # Wait for potential network activity
            print("7. Waiting for network activity to complete...")
            await page.wait_for_timeout(10000)  # Wait 10 seconds for processing
            
            # Take final screenshot
            await page.screenshot(path='C:/Users/Ryan.김준형/Documents/Projects/music_merger_project/final_result.png')
            
            print("8. Checking for results or error messages")
            # Check for any result elements
            try:
                result_element = await page.wait_for_selector('.result, #result, .error, .success, .alert', timeout=2000)
                result_text = await result_element.inner_text()
                print(f"   - Result found: {result_text}")
            except:
                print("   - No specific result element found")
            
            # Check page content for any messages
            page_content = await page.content()
            
            print("\n=== CONSOLE LOGS ===")
            for log in console_logs:
                print(f"[{log['type']}] {log['text']}")
                if log['location']:
                    print(f"    Location: {log['location']}")
            
            print("\n=== NETWORK REQUESTS ===")
            api_requests = [log for log in network_logs if '/extract' in log.get('url', '') or '/api' in log.get('url', '')]
            for log in api_requests:
                print(f"{log['type'].upper()}: {log.get('method', 'N/A')} {log['url']}")
                if log['type'] == 'response':
                    print(f"    Status: {log['status']}")
            
            # Try to get response content for API calls
            print("\n=== API RESPONSE DETAILS ===")
            for log in network_logs:
                if log['type'] == 'response' and ('/extract' in log['url'] or '/api' in log['url']):
                    try:
                        # Try to intercept response content
                        response = await page.wait_for_response(lambda response: log['url'] in response.url, timeout=1000)
                        if response:
                            response_text = await response.text()
                            print(f"Response from {log['url']}:")
                            print(f"Status: {response.status}")
                            print(f"Content: {response_text}")
                    except:
                        print(f"Could not get response content for {log['url']}")
            
            # Save logs to file
            with open('C:/Users/Ryan.김준형/Documents/Projects/music_merger_project/test_logs.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'console_logs': console_logs,
                    'network_logs': network_logs,
                    'final_url': page.url,
                    'page_title': await page.title()
                }, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"Error during test: {e}")
            await page.screenshot(path='C:/Users/Ryan.김준형/Documents/Projects/music_merger_project/error_screenshot.png')
        
        finally:
            print("\n=== TEST COMPLETE ===")
            print("Screenshots and logs saved to project directory")
            # Keep browser open for manual inspection
            input("Press Enter to close browser...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_link_extraction())