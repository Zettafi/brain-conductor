"""Shared Behave steps module"""
from dataclasses import dataclass


@dataclass
class Config:
    """
    Behave environment settings
    """

    selenium_browser: str
    selenium_driver: str
    driver_location: str
    headless: bool
    selenium_server_uri: str
    device_type: str
    browser_wait_timeout: int
    site_uri: str
