Feature: Navigation
  To be able to navigate to this website,
  as a user,
  I need navigation features

  Background:
    Given I am on the home page

  Scenario Outline: Header Navigation
    When I click the menu item <menu_item>
    Then A modal will pop up
    Examples:
      | menu_item  |
      | CONTACT US |
