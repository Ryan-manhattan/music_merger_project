#!/usr/bin/env python3
"""
Automated Playwright test script to debug the link extraction functionality
"""

import asyncio
import json
from playwright.async_api import async_playwright
import time

async def test_link_extraction():
    async with async_playwright() as p:
        # Launch browser in headless mode for automation
        browser = await p.chromium.launch(
            headless=True,  # Run headless for automation
            args=['--disable-web-security', '--disable-features=VizDisplayCompositor']
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
                'headers': dict(request.headers),
                'timestamp': time.time()
            })
            print(f"REQUEST: {request.method} {request.url}")
        
        async def handle_response(response):
            try:
                response_text = await response.text()
            except:
                response_text = "Could not read response body"
            
            network_logs.append({
                'type': 'response',
                'url': response.url,
                'status': response.status,
                'headers': dict(response.headers),
                'body': response_text,
                'timestamp': time.time()
            })
            print(f"RESPONSE: {response.status} {response.url}")
            if '/extract' in response.url or '/api' in response.url:
                print(f"  API Response Body: {response_text}")
        
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
            # Find the link input field with multiple selectors
            selectors_to_try = [
                'input[type="url"]',
                'input[placeholder*="링크"]',
                'input[name="url"]',
                '#url-input',
                'input[type="text"]',
                '.url-input',
                'input'
            ]
            
            link_input = None
            for selector in selectors_to_try:
                try:
                    link_input = await page.wait_for_selector(selector, timeout=2000)
                    print(f"   - Found input with selector: {selector}")
                    break
                except:
                    continue
            
            if not link_input:
                print("   - Could not find link input field")
                # Get all input elements for debugging
                inputs = await page.query_selector_all('input')
                print(f"   - Found {len(inputs)} input elements total")
                for i, inp in enumerate(inputs):
                    inp_type = await inp.get_attribute('type')
                    inp_name = await inp.get_attribute('name')
                    inp_id = await inp.get_attribute('id')
                    inp_placeholder = await inp.get_attribute('placeholder')
                    print(f"     Input {i}: type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}")
                
                # Try the first text input
                if inputs:
                    link_input = inputs[0]
                    print("   - Using first input element")
            
            if link_input:
                print("3. Entering YouTube URL")
                await link_input.fill('https://www.youtube.com/watch?v=RUKqwwyAiEU')
                print("   - URL entered successfully")
                
                # Take screenshot after entering URL
                await page.screenshot(path='C:/Users/Ryan.김준형/Documents/Projects/music_merger_project/after_url_input.png')
                
                print("4. Looking for extract button")
                # Find and click the extract button
                button_selectors = [
                    'button:has-text("🎵 추출")',
                    'button:has-text("추출")',
                    'input[type="submit"]',
                    'button[type="submit"]',
                    '.extract-btn',
                    '#extract-btn',
                    'button'
                ]
                
                extract_button = None
                for selector in button_selectors:
                    try:
                        extract_button = await page.wait_for_selector(selector, timeout=2000)
                        print(f"   - Found button with selector: {selector}")
                        break
                    except:
                        continue
                
                if not extract_button:
                    print("   - Could not find extract button")
                    # Get all button elements for debugging
                    buttons = await page.query_selector_all('button')
                    print(f"   - Found {len(buttons)} button elements total")
                    for i, btn in enumerate(buttons):
                        btn_text = await btn.inner_text()
                        btn_type = await btn.get_attribute('type')
                        btn_id = await btn.get_attribute('id')
                        btn_class = await btn.get_attribute('class')
                        print(f"     Button {i}: text='{btn_text}', type={btn_type}, id={btn_id}, class={btn_class}")
                    
                    # Try form submission
                    forms = await page.query_selector_all('form')
                    if forms:
                        print("   - Trying form submission instead")
                        await forms[0].evaluate('form => form.submit()')
                    else:
                        # Try the first button
                        if buttons:
                            extract_button = buttons[0]
                            print("   - Using first button element")
                
                if extract_button:
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
                    await page.wait_for_timeout(15000)  # Wait 15 seconds for processing
                    
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
                    print("   - Final page URL:", page.url)
            
            print("\n=== CONSOLE LOGS ===")
            for log in console_logs:
                print(f"[{log['type']}] {log['text']}")
                if log['location']:
                    print(f"    Location: {log['location']}")
            
            print("\n=== NETWORK ACTIVITY ===")
            for log in network_logs:
                if log['type'] == 'request':
                    print(f"REQUEST: {log.get('method', 'N/A')} {log['url']}")
                else:
                    print(f"RESPONSE: {log['status']} {log['url']}")
                    if '/extract' in log['url'] or '/api' in log['url'] or 'download' in log['url']:
                        print(f"  Body: {log.get('body', 'No body')}")
            
            # Save logs to file
            with open('C:/Users/Ryan.김준형/Documents/Projects/music_merger_project/test_logs.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'console_logs': console_logs,
                    'network_logs': network_logs,
                    'final_url': page.url,
                    'page_title': await page.title(),
                    'test_timestamp': time.time()
                }, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"Error during test: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path='C:/Users/Ryan.김준형/Documents/Projects/music_merger_project/error_screenshot.png')
        
        finally:
            await browser.close()
            print("\n=== TEST COMPLETE ===")
            print("Screenshots and logs saved to project directory")

if __name__ == "__main__":
    asyncio.run(test_link_extraction())