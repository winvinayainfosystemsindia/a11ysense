import logging
import asyncio
import fnmatch
from typing import Optional, Dict, Tuple
from common.schemas.audit import PageCredentialConfig
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class LoginService:
    async def perform_login(self, config: PageCredentialConfig) -> Tuple[bool, Dict[str, str], Dict[str, str], Optional[str], Optional[str]]:
        """
        Executes login flow based on auth_type.
        Returns: Tuple[success (bool), cookies (dict), headers (dict), error_detail (str|None), landed_url (str|None)]
        """
        cookies = {}
        headers = {}

        if config.auth_type == "bearer_token":
            # Direct Authorization Header injection
            token = config.password or config.username
            if token:
                headers["Authorization"] = f"Bearer {token}"
            return True, cookies, headers, None, config.login_url

        elif config.auth_type == "cookie":
            # Direct cookie injection
            if config.extra_fields:
                cookies.update(config.extra_fields)
            elif config.username and config.password:
                cookies[config.username] = config.password
            return True, cookies, headers, None, config.login_url

        elif config.auth_type == "form":
            # Playwright browser-based form login
            pw = None
            browser = None
            try:
                pw = await async_playwright().start()
                browser = await pw.chromium.launch(headless=True)
                
                # Setup context with normal desktop user agent
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                )
                
                page = await context.new_page()
                page.set_default_timeout(60000)  # 60s timeout for login actions

                success, cookies, headers, error_detail, landed_url = await self.perform_login_steps(config, page, context)
                
                await browser.close()
                await pw.stop()
                return success, cookies, headers, error_detail, landed_url

            except Exception as e:
                logger.exception("Error performing Playwright form login")
                try:
                    if browser:
                        await browser.close()
                    if pw:
                        await pw.stop()
                except Exception:
                    pass
                return False, {}, {}, f"Login automation error: {str(e)}", None

        return False, {}, {}, f"Unsupported auth_type: {config.auth_type}", None

    async def perform_login_steps(self, config: PageCredentialConfig, page, context) -> Tuple[bool, Dict[str, str], Dict[str, str], Optional[str], Optional[str]]:
        """
        Runs the actual login steps on an already initialized Playwright page and context.
        """
        cookies = {}
        headers = {}
        # Navigate to login URL
        logger.info(f"Navigating to login page: {config.login_url}")
        await page.goto(config.login_url, wait_until="domcontentloaded")

        # Fill username
        username_sel = config.username_field or "[name=username]"
        logger.info(f"Filling username field '{username_sel}'")
        try:
            await page.wait_for_selector(username_sel, state="visible", timeout=3000)
        except Exception:
            if username_sel == "[name=username]":
                fallbacks = ["[name=email]", "input[type=email]", "#email", "#username", "input[autocomplete=email]", "input[autocomplete=username]"]
                resolved = False
                for fb in fallbacks:
                    try:
                        logger.info(f"Default username field not found. Trying fallback selector '{fb}'")
                        await page.wait_for_selector(fb, state="visible", timeout=1500)
                        username_sel = fb
                        resolved = True
                        break
                    except Exception:
                        continue
                if not resolved:
                    raise TimeoutError(f"Username selector '{username_sel}' and fallbacks not found.")
            else:
                raise
        await page.fill(username_sel, config.username or "")

        # Fill password
        password_sel = config.password_field or "[name=password]"
        logger.info(f"Filling password field '{password_sel}'")
        try:
            await page.wait_for_selector(password_sel, state="visible", timeout=3000)
        except Exception:
            if password_sel == "[name=password]":
                fallbacks = ["input[type=password]", "#password", "input[autocomplete=current-password]"]
                resolved = False
                for fb in fallbacks:
                    try:
                        logger.info(f"Default password field not found. Trying fallback selector '{fb}'")
                        await page.wait_for_selector(fb, state="visible", timeout=1500)
                        password_sel = fb
                        resolved = True
                        break
                    except Exception:
                        continue
                if not resolved:
                    raise TimeoutError(f"Password selector '{password_sel}' and fallbacks not found.")
            else:
                raise
        await page.fill(password_sel, config.password or "")

        # Fill extra fields if any
        if config.extra_fields:
            for selector, value in config.extra_fields.items():
                try:
                    logger.info(f"Filling extra field '{selector}'")
                    await page.fill(selector, value)
                except Exception as ef:
                    logger.warning(f"Could not fill extra field '{selector}': {ef}")

        # Auto-check any checkboxes on the page (e.g., "I agree to terms", "Remember me") to satisfy form requirements
        try:
            checkboxes = await page.query_selector_all("input[type=checkbox]")
            for cb in checkboxes:
                is_checked = await cb.is_checked()
                if not is_checked:
                    logger.info("Found unchecked checkbox, checking it to satisfy form requirements...")
                    # 1. Try checking the input directly
                    await cb.check(force=True)
                    
                    # 2. Check if the submit button has become enabled
                    await asyncio.sleep(0.5)
                    is_disabled = await page.evaluate("() => { const btn = document.querySelector('button[type=submit]'); return btn ? btn.disabled : false; }")
                    if is_disabled:
                        logger.info("Submit button still disabled after direct check. Attempting to click checkbox parent elements...")
                        parent = await cb.evaluate_handle("el => el.parentElement")
                        if parent:
                            await parent.as_element().click(force=True)
                            await asyncio.sleep(0.5)
                        
                        # Check again and try closest label
                        is_disabled = await page.evaluate("() => { const btn = document.querySelector('button[type=submit]'); return btn ? btn.disabled : false; }")
                        if is_disabled:
                            label = await cb.evaluate_handle("el => el.closest('label')")
                            if label:
                                await label.as_element().click(force=True)
                                await asyncio.sleep(0.5)
        except Exception as cbe:
            logger.warning(f"Failed to check checkbox: {cbe}")

        # Check for CAPTCHA/MFA
        content = await page.content()
        if "captcha" in content.lower() or "recaptcha" in content.lower():
            return False, {}, {}, "CAPTCHA block detected on login page. Manual authentication or IP whitelisting required.", None

        # Submit form
        submit_sel = config.submit_selector or "button[type=submit]"
        logger.info(f"Clicking submit button '{submit_sel}'")
        try:
            await page.wait_for_selector(submit_sel, state="visible", timeout=3000)
        except Exception:
            if submit_sel == "button[type=submit]":
                fallbacks = ["button:has-text('Sign In')", "button:has-text('Login')", "button:has-text('Log In')", "input[type=submit]", "button", "a:has-text('Login')", "a:has-text('Sign In')"]
                resolved = False
                for fb in fallbacks:
                    try:
                        logger.info(f"Default submit selector not found. Trying fallback selector '{fb}'")
                        await page.wait_for_selector(fb, state="visible", timeout=1500)
                        submit_sel = fb
                        resolved = True
                        break
                    except Exception:
                        continue
                if not resolved:
                    raise TimeoutError(f"Submit selector '{submit_sel}' and fallbacks not found.")
            else:
                raise
        
        # Wait for URL to change from the login URL, or wait for navigation/load state
        login_url_before = page.url
        await page.click(submit_sel)
        
        try:
            # Wait up to 8 seconds for the URL to change to something else
            await page.wait_for_function(f"() => window.location.href !== '{login_url_before}'", timeout=8000)
        except Exception:
            # If it didn't change, wait for network idle to make sure any lazy loads finish
            try:
                await page.wait_for_load_state("networkidle", timeout=2000)
            except Exception:
                pass

        # Post-login URL verification
        current_url = page.url
        logger.info(f"URL after form submit: {current_url}")

        # Check for post-login failures/errors shown on the page
        content_after = await page.content()
        if "invalid credentials" in content_after.lower() or "incorrect password" in content_after.lower() or "login failed" in content_after.lower():
            return False, {}, {}, "Authentication failed: Invalid credentials or login rejected by target application.", None

        if "two-factor" in content_after.lower() or "mfa" in content_after.lower() or "otp" in content_after.lower():
            return False, {}, {}, "Multi-factor authentication (MFA) challenge detected. MFA is not supported in automated audits.", None

        if config.post_login_url_pattern:
            if not fnmatch.fnmatch(current_url, config.post_login_url_pattern) and config.post_login_url_pattern not in current_url:
                return False, {}, {}, f"Login verification failed. Expected post-login URL to match '{config.post_login_url_pattern}', but landed on '{current_url}'.", None

        # Extract cookies from browser context
        pw_cookies = await context.cookies()
        extracted_cookies = {c["name"]: c["value"] for c in pw_cookies}

        # Extract localStorage and sessionStorage items to search for Bearer/JWT tokens
        try:
            storage_state = await page.evaluate("""() => {
                const data = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const k = localStorage.key(i);
                    data[k] = localStorage.getItem(k);
                }
                for (let i = 0; i < sessionStorage.length; i++) {
                    const k = sessionStorage.key(i);
                    data[k] = sessionStorage.getItem(k);
                }
                return data;
            }""")
            
            # Search for JWT or other auth tokens in storage
            auth_token = None
            for key, val in storage_state.items():
                if not val or not isinstance(val, str):
                    continue
                
                # Remove quotes if stringified JSON
                clean_val = val.strip()
                if clean_val.startswith('"') and clean_val.endswith('"'):
                    clean_val = clean_val[1:-1]
                    
                # Check for JWT token pattern (starts with eyJ)
                if clean_val.startswith("eyJ") and len(clean_val) > 50:
                    logger.info(f"Detected JWT token in storage key '{key}'")
                    auth_token = clean_val
                    break
                # Check for generic token keys if value looks like a token
                if any(k in key.lower() for k in ["token", "jwt", "access_token", "accesstoken", "id_token"]) and len(clean_val) > 10:
                    logger.info(f"Detected potential auth token in storage key '{key}'")
                    auth_token = clean_val
                    break
                    
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
        except Exception as se:
            logger.warning(f"Failed to check local/session storage for tokens: {se}")

        # Success if either cookies were set or auth headers were extracted
        return True, extracted_cookies, headers, None, current_url

    async def perform_login_with_state(self, config: PageCredentialConfig) -> Tuple[bool, Dict[str, str], Dict[str, str], Optional[str], Optional[str], Optional[dict]]:
        """
        Executes form login and captures the full browser storage state (cookies + local storage).
        """
        import urllib.parse
        if config.auth_type != "form":
            # Direct headers/cookies
            cookies = {}
            headers = {}
            if config.auth_type == "bearer_token":
                token = config.password or config.username
                if token:
                    headers["Authorization"] = f"Bearer {token}"
            elif config.auth_type == "cookie":
                if config.extra_fields:
                    cookies.update(config.extra_fields)
                elif config.username and config.password:
                    cookies[config.username] = config.password
            
            # Construct a basic storage_state dictionary
            parsed_url = urllib.parse.urlparse(config.login_url)
            domain = parsed_url.netloc
            pw_cookies = []
            for k, v in cookies.items():
                pw_cookies.append({
                    "name": k,
                    "value": v,
                    "domain": domain,
                    "path": "/"
                })
            
            storage_state = {
                "cookies": pw_cookies,
                "origins": []
            }
            return True, cookies, headers, None, config.login_url, storage_state

        pw = None
        browser = None
        try:
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=True)
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            page.set_default_timeout(30000)

            success, cookies, headers, error_detail, landed_url = await self.perform_login_steps(config, page, context)
            
            storage_state = None
            if success:
                storage_state = await context.storage_state()

            await browser.close()
            await pw.stop()
            return success, cookies, headers, error_detail, landed_url, storage_state

        except Exception as e:
            logger.exception("Error performing Playwright form login with state")
            try:
                if browser:
                    await browser.close()
                if pw:
                    await pw.stop()
            except Exception:
                pass
            return False, {}, {}, f"Login automation error: {str(e)}", None, None

login_service = LoginService()
