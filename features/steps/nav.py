from behave import given, when, then, use_step_matcher
from behave.runner import Context

from features.steps.selenium_steps import click, wait_for_element_visibility

use_step_matcher("parse")


@given("I click the menu item {menu_item}")
@when("I click the menu item {menu_item}")
def click_menu_item(context: Context, menu_item: str):
    if context.selenium.is_mobile:
        hamburger_menu_xpath = "//span[contains(@class, 'navbar-toggler-icon')]"
        click(context, hamburger_menu_xpath)

    xpath = f"//a[contains(@class, 'nav-link') and contains(text(), '{menu_item}')]"
    click(context, xpath)


@then("A modal will pop up")
def wait_pop_up_modal(context):
    modal_xpath = '//div[@class="modal fade show"]'
    wait_for_element_visibility(context, modal_xpath)
