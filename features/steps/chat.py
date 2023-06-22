from behave import given, when, then, use_step_matcher
from behave.runner import Context
from selenium.common import TimeoutException

from features.steps.selenium_steps import (
    fill_field,
    get_element_value,
    browse_to_page,
    click,
    wait_for_element_presence,
)

use_step_matcher("parse")


@given("I am on the home page")
def am_on_the_home_page(context: Context):
    browse_to_page(context, "/")


@when('I enter "{text}" in the input field')
def enter_value_in_the_field(context: Context, text: str):
    fill_field(context, "message", text)


@when("I press {text}")
@when("press {text}")
def submit_the_form(context: Context, text):
    click(context, f"//button[@class = '{text}']")


@then('I should see "{text}" in the response from "{persona}"')
def should_see_text_in_response_from_persona(context: Context, text: str, persona: str):
    actual = response_from_persona(context, persona)
    assert (
        text.lower() in actual.lower()
    ), f'Response "{actual}" did not contain "{text}"'


@then('I should see a response from "{persona}"')
def response_from_persona(context: Context, persona: str):
    try:
        return get_element_value(context, f'//div[contains(@data-is, "{persona}")]/..')
    except (TimeoutException, TimeoutError):
        raise Exception(f"Unable to locate a response from {persona}")


@then("I should see a response from one of: {personas}")
def response_from_one_of_personas(context: Context, personas: str):
    personas_list = (
        [persona.strip() for persona in personas.split(",")] if personas else []
    )
    contains_list = [f'contains(@data-is, "{persona}")' for persona in personas_list]
    xpath = "//div[" + " or ".join(contains_list) + "]"
    try:
        return wait_for_element_presence(context, xpath)
    except (TimeoutException, TimeoutError):
        raise Exception(f"Unable to locate a response from any of {personas}")


@then("I should see a response from each of: {personas}")
def response_from_each_of_personas(context: Context, personas: str):
    personas_list = (
        []
        if personas == "N/A"
        else [persona.strip() for persona in personas.split(",")]
    )
    missing_personas = []
    for persona in personas_list:
        xpath = f'//div[contains(@data-is, "{persona}")]'
        try:
            return wait_for_element_presence(context, xpath)
        except (TimeoutException, TimeoutError):
            missing_personas.append(persona)
    assert (
        not personas_list
    ), f"Could not find personas in responses: {missing_personas}"
