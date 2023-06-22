from behave import given, when, use_step_matcher
from behave.runner import Context

from features.steps.selenium_steps import click

use_step_matcher("parse")


@given("I click the menu item {menu_item}")
@when("I click the menu item {menu_item}")
def click_menu_item(context: Context, menu_item: str):
    if context.selenium.is_mobile:
        hamburger_menu_xpath = "//span[contains(@class, 'navbar-toggler-icon')]"
        click(context, hamburger_menu_xpath)

    xpath = f"//a[contains(@class, 'nav-link') and contains(text(), '{menu_item}')]"
    click(context, xpath)
