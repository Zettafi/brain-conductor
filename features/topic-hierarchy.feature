Feature: Persona Hierarchy
  In order to get the best answer
  As a persona
  I will respond based on a hierarchy that ensures the most knowledgeable persona answers

  Background:
    Given I am on the home page

  #noinspection LongLine
  Scenario Outline: Primary and secondary personas answer the topic
    When I enter "I want to know more about the topic <topic> from an expert on the topic" in the input field
    And I press send
    Then I should see a response from one of: <primaries>
    And I should see a response from each of: <secondaries>

    Examples:
      | topic          | primaries                       | secondaries                                                   |
      | Science        | Scientist Steve                 | N/A                                                           |
      | Entertainment  | Melodic Mike, Fashionable Fiona | Melodic Mike, Fashionable Fiona, Culinary Colin, Trekking Tom |
      | Health         | Doctor Darby                    | Serene Sam, Relationship Ronit                                |
      | Food           | Culinary Colin                  | Trekking Tom                                                  |
      | Politics       | Conservative Clark              | Educated Emily, Comical Chris                                 |
      | Sports         | Sporty Scott                    | N/A                                                           |
      | Travel         | Trekking Tom                    | N/A                                                           |
      | Education      | Educated Emily                  | Educated Emily, Scientist Steve                               |
      | Finance        | Investing Isabel                | Techno Tony                                                   |
      | Fashion        | Fashionable Fiona               | Melodic Mike                                                  |
      | Gaming         | Gaming Gabby                    | N/A                                                           |
      | Literature     | Narrative Nick                  | N/A                                                           |
      | Art            | Artistic Abby                   | Narrative Nick, Melodic Mike                                  |
      | Environment    | Eco Eva                         | N/A                                                           |
      | Home Repair    | Handy Harry                     | N/A                                                           |
      | Philosophy     | Serene Sam                      | Comical Chris, Trekking Tom                                   |
      | Business       | Enterprising Erin               | Techno Tony, Policy Pete,  Investing Isabel                   |
      | Animals        | Zoology Zach                    | N/A                                                           |
      | Humor          | Comical Chris                   | Techno Tony, Narrative Nick                                   |
      | Technology     | Techno Tony                     | Scientist Steve, Enterprising Erin                            |
      | Relationships  | Relationship Ronit              | Doctor Darby                                                  |
      | Cryptocurrency | Crypto Carl, Bearish Bart       | N/A                                                           |
