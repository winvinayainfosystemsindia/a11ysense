import logging
import asyncio
import fnmatch
from typing import Optional, Dict, Tuple
from common.schemas.audit import PageCredentialConfig
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class LoginService:
    async def perform_login(self, config: PageCredentialConfig) -> Tuple[bool, Dict[str, str], Dict[str, str], Optional[str]]:
        """
        Executes login flow based on auth_type.
        Returns: Tuple[success (bool), cookies (dict), headers (dict), error_detail (str|None)]
        """
        cookies = {}
        headers = {}

        if config.auth_type == "bearer_token":
            # Direct Authorization Header injection
            token = config.password or config.username
            if token:
                headers["Authorization"] = f"Bearer {token}"
            return True, cookies, headers, None

        elif config.auth_type == "cookie":
            # Direct cookie injection
            if config.extra_fields:
                cookies.update(config.extra_fields)
            elif config.username and config.password:
                cookies[config.username] = config.password
            return True, cookies, headers, None

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
                page.set_default_timeout(15000)  # 15s timeout for login actions

                # Navigate to login URL
                logger.info(f"Navigating to login page: {config.login_url}")
                await page.goto(config.login_url, wait_until="networkidle")

                # Fill username
                username_sel = config.username_field or "[name=username]"
                logger.info(f"Filling username field '{username_sel}'")
                await page.wait_for_selector(username_sel, state="visible", timeout=5000)
                await page.fill(username_sel, config.username or "")

                # Fill password
                password_sel = config.password_field or "[name=password]"
                logger.info(f"Filling password field '{password_sel}'")
                await page.wait_for_selector(password_sel, state="visible", timeout=5000)
                await page.fill(password_sel, config.password or "")

                # Fill extra fields if any
                if config.extra_fields:
                    for selector, value in config.extra_fields.items():
                        try:
                            logger.info(f"Filling extra field '{selector}'")
                            await page.fill(selector, value)
                        except Exception as ef:
                            logger.warning(f"Could not fill extra field '{selector}': {ef}")

                # Check for CAPTCHA/MFA
                content = await page.content()
                if "captcha" in content.lower() or "recaptcha" in content.lower():
                    await browser.close()
                    await pw.stop()
                    return False, {}, {}, "CAPTCHA block detected on login page. Manual authentication or IP whitelisting required."

                # Submit form
                submit_sel = config.submit_selector or "button[type=submit]"
                logger.info(f"Clicking submit button '{submit_sel}'")
                await page.click(submit_sel)

                # Wait for navigation/network idle to complete login redirect chain
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    logger.warning("Timeout waiting for network idle after form submit, continuing...")

                # Post-login URL verification
                current_url = page.url
                logger.info(f"URL after form submit: {current_url}")

                # Check for post-login failures/errors shown on the page
                content_after = await page.content()
                if "invalid credentials" in content_after.lower() or "incorrect password" in content_after.lower() or "login failed" in content_after.lower():
                    await browser.close()
                    await pw.stop()
                    return False, {}, {}, "Authentication failed: Invalid credentials or login rejected by target application."

                if "two-factor" in content_after.lower() or "mfa" in content_after.lower() or "otp" in content_after.lower():
                    await browser.close()
                    await pw.stop()
                    return False, {}, {}, "Multi-factor authentication (MFA) challenge detected. MFA is not supported in automated audits."

                if config.post_login_url_pattern:
                    if not fnmatch.fnmatch(current_url, config.post_login_url_pattern) and config.post_login_url_pattern not in current_url:
                        await browser.close()
                        await pw.stop()
                        return False, {}, {}, f"Login verification failed. Expected post-login URL to match '{config.post_login_url_pattern}', but landed on '{current_url}'."

                # Extract cookies from browser context
                pw_cookies = await context.cookies()
                extracted_cookies = {c["name"]: c["value"] for c in pw_cookies}

                await browser.close()
                await pw.stop()

                if not extracted_cookies:
                    return False, {}, {}, "Login succeeded but no cookies were generated by the application."

                return True, extracted_cookies, {}, None

            except Exception as e:
                logger.exception("Error performing Playwright form login")
                try:
                    if browser:
                        await browser.close()
                    if pw:
                        await pw.stop()
                except Exception:
                    pass
                return False, {}, {}, f"Login automation error: {str(e)}"

        return False, {}, {}, f"Unsupported auth_type: {config.auth_type}"

login_service = LoginService()
