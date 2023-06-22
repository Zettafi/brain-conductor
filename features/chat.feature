Feature: I can have a proper conversation with the bot
  In order to get information
  As a user
  I can interact with the chatbot

  Background:
    Given I am on the home page

  Scenario: My input is echoed back
    When I enter "test" in the input field
    And I press send
    Then I should see "test" in the response from "You"
