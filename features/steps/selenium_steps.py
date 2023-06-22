import os
import time
from enum import Enum
from typing import NamedTuple, Callable, Optional, Tuple

import requests
from behave.runner import Context
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common import TimeoutException, StaleElementReferenceException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import BaseWebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

try:  # Load .env if dotenv is installed
    # noinspection PyUnresolvedReferences
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class DeviceType(Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"


class SeleniumContext(NamedTuple):
    test_url: str
    browser_wait_timeout: int
    is_mobile: bool
    browse_to_page: Callable
    click: Callable
    force_click: Callable
    element_is_present: Callable
    is_page_title: Callable
    get_element_value: Callable
    fill_field: Callable
    send_enter_key: Callable
    window_size: Tuple[int, int]
    browser: Optional[BaseWebDriver] = None


def check_selenium_ready(selenium_server_uri):
    resp = requests.get(selenium_server_uri + "/status")
    return resp.json()["value"]["ready"]


def before_all(context):
    if context.config.selenium_driver not in ("local", "remote"):
        raise ValueError("Unknown SELENIUM_DRIVER of " + context.config.selenium_driver)
    if context.config.device_type == DeviceType.DESKTOP.value:
        window_size = (1920, 1080)
        device_type = DeviceType.DESKTOP
    elif context.config.device_type == DeviceType.MOBILE.value:
        window_size = (375, 667)
        device_type = DeviceType.MOBILE
    else:
        raise ValueError(f"Unknown DEVICE_TYPE of \"{context['config'].device_type}\"")

    context.selenium = SeleniumContext(
        test_url=context.config.site_uri,
        browser_wait_timeout=context.config.browser_wait_timeout,
        is_mobile=device_type == DeviceType.MOBILE,
        browse_to_page=browse_to_page,
        click=click,
        force_click=force_click,
        element_is_present=element_is_present,
        is_page_title=is_page_title,
        get_element_value=get_element_value,
        fill_field=fill_field,
        send_enter_key=send_enter_key,
        window_size=window_size,
    )


def before_scenario(context: Context, _scenario):
    context.selenium_browser = get_web_driver(
        context.config.selenium_browser,
        context.config.headless,
        context.config.selenium_driver,
        context.config.selenium_server_uri,
        context.config.driver_location,
        context.selenium.window_size,
    )


def after_scenario(context: Context, _scenario):
    if hasattr(context, "selenium_browser") and context.selenium_browser:
        context.selenium_browser.quit()


def get_web_driver(
    selenium_browser,
    headless,
    driver_type,
    selenium_server_uri,
    driver_location,
    window_size,
):
    extra_local_args = dict()
    if selenium_browser == "chrome" or selenium_browser == "edge":
        if selenium_browser == "chrome":
            local_driver = webdriver.Chrome
            if driver_location is None:
                driver_location = "/usr/local/bin/chromedriver"
            options = webdriver.ChromeOptions()
        else:
            os.putenv("MSEDGEDRIVER_TELEMETRY_OPTOUT", "1")  # Turn off telemetry
            local_driver = webdriver.Edge
            if driver_location is None:
                driver_location = "/usr/local/bin/msedgedriver"
            options = webdriver.EdgeOptions()
        options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        options.add_argument("--start-maximised")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--whitelisted-ips")
        options.add_argument("--whitelisted-origins")
        if headless or driver_type == "remote":
            options.add_argument("--headless")
    elif selenium_browser == "firefox":
        local_driver = webdriver.Firefox
        if driver_location is None:
            driver_location = "/usr/local/bin/geckodriver"
        extra_local_args["log_output"] = "/dev/null"
        options = webdriver.FirefoxOptions()
        options.add_argument(f"--width={window_size[0]}")
        options.add_argument(f"--height={window_size[1]}")
        if headless or driver_type == "remote":
            options.add_argument("-headless")
    else:
        raise ValueError(f"Unsupported browser {selenium_browser}")

    if driver_type == "remote":
        while not check_selenium_ready(selenium_server_uri):
            time.sleep(5)
        browser = webdriver.Remote(
            options=options, command_executor=selenium_server_uri
        )
    else:
        service = Service(executable_path=driver_location, **extra_local_args)
        browser = local_driver(options=options, service=service)

    return browser


def wait_for(context: Context, expected_condition: EC) -> WebElement:
    return WebDriverWait(
        context.selenium_browser, context.selenium.browser_wait_timeout
    ).until(expected_condition)


def wait_for_element_clickability(context: Context, xpath) -> WebElement:
    try:
        return wait_for(context, EC.element_to_be_clickable((By.XPATH, xpath)))
    except TimeoutException:
        raise TimeoutError(f"Timeout waiting for {xpath} to be clickable.")


def wait_for_element_presence(context: Context, xpath) -> WebElement:
    try:
        return wait_for(context, EC.presence_of_element_located((By.XPATH, xpath)))
    except TimeoutException:
        raise TimeoutError(f"Timeout waiting for {xpath} to be present.")


def wait_for_element_visibility(context: Context, xpath) -> WebElement:
    try:
        return wait_for(context, EC.visibility_of_element_located((By.XPATH, xpath)))
    except TimeoutException:
        raise TimeoutError(f"Timeout waiting for {xpath} to be visible.")


def wait_for_url_change(context: Context, next_url) -> WebElement:
    try:
        return wait_for(context, lambda browser: browser.current_url == next_url)
    except TimeoutException:
        raise TimeoutError(f"Timeout waiting for {next_url} to be loaded.")


def browse_to(context: Context, target: str):
    context.selenium_browser.get(target)


def browse_to_page(context: Context, target: str):
    browse_to(context, context.selenium.test_url + "/" + target)


def click(context: Context, xpath):
    element = wait_for_element_clickability(context, xpath)
    element.click()


def force_click(context: Context, xpath):
    element = wait_for_element_presence(context, xpath)
    context.selenium_browser.execute_script(
        "return arguments[0].scrollIntoView(true);", element
    )
    ActionChains(context.selenium_browser).move_to_element(element).click(
        element
    ).perform()


def element_is_present(context: Context, xpath):
    try:
        wait_for_element_presence(context, xpath)
        return True
    except TimeoutError:
        return False


def is_page_title(context: Context, title):
    try:
        wait_for(context, EC.title_is(title))
        return True
    except TimeoutException:
        return False


def get_element_value(context: Context, xpath) -> str:
    timeout = time.time() + context.selenium.browser_wait_timeout
    while time.time() < timeout:
        try:
            return wait_for_element_presence(context, xpath).text
        except StaleElementReferenceException:
            time.sleep(0.001)
            continue


def fill_field(context: Context, field_name, value):
    field = wait_for_element_presence(context, f"//input[@name='{field_name}']")
    field.send_keys(value)


def send_enter_key(context: Context):
    context.selenium_browser.find_element(By.XPATH, "/html/body").send_keys(Keys.ENTER)
