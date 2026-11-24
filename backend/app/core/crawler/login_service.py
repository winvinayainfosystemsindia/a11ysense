import logging
import asyncio
import fnmatch
import urllib.parse
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
                page.set_default_timeout(120000)  # 120s timeout for login actions

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
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        # If page is a landing page with a Sign In link/button instead of direct input fields, click it
        try:
            has_visible_input = await page.evaluate("""() => {
                const inputs = Array.from(document.querySelectorAll('input:not([type=hidden])'));
                return inputs.some(i => i.offsetParent !== null && !i.disabled);
            }""")
            if not has_visible_input:
                logger.info("No visible input fields on initial page. Checking for Sign In / Login CTA...")
                signin_selectors = [
                    "a.zgh-login", "a.zws-login-cta",
                    "a:has-text('Sign In')", "a:has-text('Sign in')", "a:has-text('Login')", "a:has-text('Log In')",
                    "button:has-text('Sign In')", "button:has-text('Sign in')", "button:has-text('Login')", "button:has-text('Log In')"
                ]
                for s_sel in signin_selectors:
                    try:
                        s_btn = await page.wait_for_selector(s_sel, state="visible", timeout=2000)
                        if s_btn:
                            logger.info(f"Clicking Sign In CTA '{s_sel}' to reach login form...")
                            await s_btn.click()
                            try:
                                await page.wait_for_load_state("networkidle", timeout=8000)
                            except Exception:
                                pass
                            break
                    except Exception:
                        continue
        except Exception as lpe:
            logger.debug(f"Landing page check error: {lpe}")

        # Fill username
        username_sel = config.username_field or "[name=username]"
        logger.info(f"Filling username field '{username_sel}'")
        try:
            await page.wait_for_selector(username_sel, state="visible", timeout=5000)
        except Exception:
            fallbacks = [
                "#login_id", "[name=LOGIN_ID]", "input[name=LOGIN_ID]",
                "[name=username]", "[name=email]", "input[type=email]", "#email", "#username",
                "input[autocomplete=email]", "input[autocomplete=username]"
            ]
            resolved = False
            for fb in fallbacks:
                try:
                    logger.info(f"Trying username fallback selector '{fb}'")
                    await page.wait_for_selector(fb, state="visible", timeout=2000)
                    username_sel = fb
                    resolved = True
                    break
                except Exception:
                    continue
            if not resolved:
                raise TimeoutError(f"Username selector '{username_sel}' and fallbacks not found.")

        await page.fill(username_sel, config.username or "")

        # Multi-step login check (e.g. Zoho Accounts, Google, Microsoft):
        # If there is a visible Next/Continue button, click it to transition to password step
        next_selectors = [
            "#nextbtn", "button#nextbtn", "button:has-text('Next')", "button:has-text('Continue')",
            "input[type=button][value='Next']", "input[type=button][value='Continue']"
        ]
        next_clicked = False
        for nsel in next_selectors:
            try:
                el = await page.query_selector(nsel)
                if el and await el.is_visible():
                    logger.info(f"Found visible multi-step next button '{nsel}'; clicking to advance to password step...")
                    await el.click()
                    next_clicked = True
                    await page.wait_for_timeout(1500)
                    break
            except Exception:
                continue

        password_sel = config.password_field or "[name=password]"
        if not next_clicked:
            try:
                if not await page.is_visible(password_sel):
                    logger.info("Password field not yet visible; pressing Enter in username field...")
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(1500)
            except Exception:
                pass

        # Locate password field (prioritizing #password and [name=PASSWORD] for multi-step providers like Zoho)
        pwd_fallbacks = [
            "#password", "[name=PASSWORD]", "input[name=PASSWORD]",
            "input[type=password]", "[name=password]", "#pass", "input[autocomplete=current-password]"
        ]
        if password_sel and password_sel != "[name=password]":
            pwd_fallbacks = [password_sel] + [f for f in pwd_fallbacks if f != password_sel]

        resolved_pwd = False
        for pfb in pwd_fallbacks:
            try:
                await page.wait_for_selector(pfb, state="visible", timeout=3000)
                password_sel = pfb
                resolved_pwd = True
                break
            except Exception:
                continue
        if not resolved_pwd:
            raise TimeoutError(f"Password field could not be found with fallbacks: {pwd_fallbacks}")

        logger.info(f"Filling password field '{password_sel}'")
        await page.fill(password_sel, config.password or "")

        # Fill extra fields if any
        if config.extra_fields:
            for selector, value in config.extra_fields.items():
                try:
                    logger.info(f"Filling extra field '{selector}'")
                    await page.fill(selector, value)
                except Exception as ef:
                    logger.warning(f"Could not fill extra field '{selector}': {ef}")

        # Check for an active, visible CAPTCHA challenge
        is_captcha_active = False
        try:
            is_captcha_active = await page.evaluate("""() => {
                const selectors = [
                    'iframe[src*="recaptcha"]', 'iframe[src*="hcaptcha"]', 'iframe[src*="turnstile"]',
                    '#captcha', 'input[name="captcha"]', '.g-recaptcha', '.h-captcha', '#captcha-container'
                ];
                for (const sel of selectors) {
                    const els = document.querySelectorAll(sel);
                    for (const el of els) {
                        const style = window.getComputedStyle(el);
                        if (style && style.display !== 'none' && style.visibility !== 'hidden' && el.offsetWidth > 0 && el.offsetHeight > 0) {
                            return true;
                        }
                    }
                }
                return false;
            }""")
        except Exception:
            is_captcha_active = False

        if is_captcha_active:
            return False, {}, {}, "CAPTCHA block detected on login page. Manual authentication or IP whitelisting required.", None

        # Submit form: resolve submit selector with fallbacks (e.g. #nextbtn on Zoho Accounts)
        submit_sel = config.submit_selector or "button[type=submit]"
        submit_fallbacks = [
            "#nextbtn", "button#nextbtn", "button[type=submit]",
            "button:has-text('Sign In')", "button:has-text('Sign in')", "button:has-text('Login')",
            "button:has-text('Log In')", "button:has-text('Next')", "input[type=submit]"
        ]
        if submit_sel and submit_sel != "button[type=submit]":
            submit_fallbacks = [submit_sel] + [f for f in submit_fallbacks if f != submit_sel]

        resolved_submit = False
        for sfb in submit_fallbacks:
            try:
                await page.wait_for_selector(sfb, state="visible", timeout=3000)
                submit_sel = sfb
                resolved_submit = True
                break
            except Exception:
                continue
        if not resolved_submit:
            raise TimeoutError(f"Submit selector could not be found with fallbacks: {submit_fallbacks}")

        logger.info(f"Clicking submit button '{submit_sel}'")
        
        login_url_before = page.url
        await page.click(submit_sel)
        
        # Wait up to 30 seconds for authentication to complete and transition to the target app
        target_netloc = None
        if config.post_login_url_pattern:
            parsed_pat = urllib.parse.urlparse(config.post_login_url_pattern)
            if parsed_pat.netloc:
                target_netloc = parsed_pat.netloc.lower()

        try:
            if target_netloc:
                logger.info(f"Waiting for navigation to target domain '{target_netloc}'...")
                await page.wait_for_url(lambda u: target_netloc in u, timeout=30000)
            else:
                await page.wait_for_url(
                    lambda u: ("login" not in u.lower() and "signin" not in u.lower()) or (u != login_url_before and "accounts." not in u.lower()),
                    timeout=30000
                )
        except Exception as we:
            logger.debug(f"wait_for_url error (proceeding to check current state): {we}")

        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
            await page.wait_for_timeout(3000)
        except Exception:
            pass

        # Post-login URL verification
        current_url = page.url
        logger.info(f"URL after form submit: {current_url}")

        # If post_login_url_pattern is provided, navigate there if needed and target domain has loaded
        if config.post_login_url_pattern and config.post_login_url_pattern.startswith("http"):
            if current_url != config.post_login_url_pattern and ("login" not in current_url.lower() and "signin" not in current_url.lower()):
                logger.info(f"Navigating to designated post-login target: {config.post_login_url_pattern}")
                try:
                    await page.goto(config.post_login_url_pattern, wait_until="domcontentloaded")
                    await page.wait_for_timeout(3000)
                    current_url = page.url
                except Exception as ple:
                    logger.warning(f"Could not navigate to post_login_url_pattern: {ple}")

        # Check for post-login failures/errors shown on the page
        # Only check failure indicators if we haven't successfully transitioned to the authenticated destination
        is_on_app = False
        if config.post_login_url_pattern:
            if config.post_login_url_pattern in current_url or fnmatch.fnmatch(current_url, config.post_login_url_pattern):
                is_on_app = True
        if not is_on_app and "login" not in current_url.lower() and "signin" not in current_url.lower():
            is_on_app = True

        if not is_on_app:
            content_after = await page.content()
            content_lower = content_after.lower()
            if "invalid credentials" in content_lower or "incorrect password" in content_lower or "login failed" in content_lower:
                return False, {}, {}, "Authentication failed: Invalid credentials or login rejected by target application.", None

            # Look for active MFA challenge inputs or specific phrases on visible page
            has_mfa = False
            try:
                has_mfa = await page.evaluate("""() => {
                    const text = (document.body ? document.body.innerText : '').toLowerCase();
                    const phrases = ['two-factor authentication', 'enter verification code', 'enter the 6-digit code', 'enter otp', 'authenticator app'];
                    if (phrases.some(p => text.includes(p))) return true;
                    const mfaInput = document.querySelector('input[name*="otp" i], input[name*="totp" i], input[id*="totp" i], input[autocomplete="one-time-code"]');
                    return !!(mfaInput && mfaInput.offsetParent !== null);
                }""")
            except Exception:
                has_mfa = False

            if has_mfa:
                return False, {}, {}, "Multi-factor authentication (MFA) challenge detected. MFA is not supported in automated audits.", None

            if config.post_login_url_pattern and not config.post_login_url_pattern.startswith("http"):
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
            page.set_default_timeout(120000)

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
