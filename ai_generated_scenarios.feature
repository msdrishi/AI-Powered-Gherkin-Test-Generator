Feature: Validate navigation menu functionality

  Scenario: Navigate to Overall Survival page from Results dropdown
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the "Results" menu
    And clicks on the "Overall Survival" link
    Then the page URL should change to "https://www.tivdak.com/patient-stories/study-results/"

  Scenario: Navigate to Objective Response page from Results dropdown
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the "Results" menu
    And clicks on the "Objective Response" link
    Then the page URL should change to "https://www.tivdak.com/patient-stories/study-results/"

  Scenario: Navigate to Understanding the Data page from Results dropdown
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the "Results" menu
    And clicks on the "Understanding the Data" link
    Then the page URL should change to "https://www.tivdak.com/patient-stories/study-results/understanding-the-data/"

  Scenario: Navigate to Downloads page from Support dropdown
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the "Support" menu
    And clicks on the "Downloads" link
    Then the page URL should change to "https://www.tivdak.com/patient-stories/resources-and-support/"

  Scenario: Navigate to Pfizer Oncology Together page from Support dropdown
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the "Support" menu
    And clicks on the "Pfizer Oncology Together" link
    Then the page URL should change to "https://www.tivdak.com/patient-stories/resources-and-support/"

  Scenario: Navigate to TivdakTexts page from Support dropdown
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the "Support" menu
    And clicks on the "TivdakTexts" link
    Then the page URL should change to "https://www.tivdak.com/patient-stories/resources-and-support/"

  Scenario: Navigate to Advocacy Groups page from Support dropdown
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the "Support" menu
    And clicks on the "Advocacy Groups" link
    Then the page URL should change to "https://www.tivdak.com/patient-stories/resources-and-support/"

  Scenario: Navigate to Support Videos page from Support dropdown
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the "Support" menu
    And clicks on the "Support Videos" link
    Then the page URL should change to "https://www.tivdak.com/patient-stories/resources-and-support/support-videos/"