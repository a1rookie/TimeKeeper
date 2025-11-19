### Databases
* You will have your own dedicated postgresql database with your name on it against which you will do development. You will keep it up to date by running alembic migrations. Ask a dev lead if you need a database with your name on it. Please do not use someone else's database - that will mess with their development and testing.
* There should be no stored procedures for Bonaventure
* Alembic Migrations:
    * Test upgrade and downgrade to make sure your Alembic migration really works
    * Once merged into the development branch, a migration may never be touched again. Instead, create a new migration to make the needed change
### Git
#### Branches
* Branches should be prefixed with feature if this is a normal story, or hotfix if this is a break fix, along with the story (e.g. ODSBONVENT-20) plus our name on the branch. e.g. feature/ODSBONVENT-20-richard
    * In general, feature branches are created from an up to date develop branches and have Merge Requests back into the develop branch
    * hotfix branches are for production break fix branches and should be confirmed as required from a dev lead. These branches should have Merge Requests into both the develop and master branches.
* Perform a rebase before pushing your branch to GitLab for a Merge Request
* Try not to work on a branch for more than a couple of days, or be ready to rebase frequently to keep up with changes
#### Commits
* All commits must have the story listed on it (e.g. ODSBONVENT-20). Note both Bonaventure Git repos will not allow you to push a branch to GitLab without a valid story in the commit message.
* Commit smaller pieces for each commit. This makes it easier to find and fix breaks from a specific commit.
* Commit messages should explain what the commit is doing.
    * Good commit message: ODSBONVENT-20: Adding ability to check access against the roles for a user from the database.
    * Bad commit message: Another Change
### Merge Requests
* At least one maintainer must review your Merge Request before it can be merged, and maintainers must have another maintainer review their code before merging.
    * Currently, as of 2021-02-21. only Brandon and Richard are maintainers in the git repos
* Maintainers must keep up with merge requests - MRs should not sit more than a day without comments or merges.
* After modifying the code to address the reviewer's comments, please mark the comment (discussion) as resolved. If follow-up discussion is required, leave the discussion open. It is strongly encouraged not to approve the merge request with any unresolved discussion. (Gitlab documentation on discussions: https://docs.gitlab.com/ee/user/discussions/)
* Smaller Merge Requests makes it easier for us to review.
    * This may mean that a larger story is broken up into smaller Merge Requests as the story is developed with working sections for review and comment and merging
* There are always opinions on how code could be written better. However, unless there is a demonstrable reason, like maintainability, code not implemented the way you prefer is not grounds to not approve a merge request. Document your opinion, and have the discussion, but don't decline a Merge Request.
* Put a `WIP:` in front of your Merge Request Title to get feedback without expecting that Merge Request to be approved (yet).
### Source Code
* Methods should not be more than 20-30 lines of code. Break it up if it is longer than that. Documentation doesn't really count against that - but we want to be able to easily see a method from beginning to end without requiring a 42 inch 4k monitor.
* DRY up the code you write (Don't Repeat Yourself). If a reviewer sees the same set of code 2 or more times, you will be asked to DRY it up.
* Expect someone in the future other than yourself will change the code you wrote.
* Document code - This is about maintainable code. Less documentation means it is more difficult to understand the code a year from now. Over documentation is always preferred to under-documentation.
* Our code is our work product – Be masters at our craft and not apprentices. Be deliberate and precise about the work we produce. Show pride in our work product.
* Quality is much more important than quantity.
* No passwords go into source control. Do not violate this rule.
* Any deliberate technical debt needs to have a Jira ticket to reflect future refactoring work will be needed.  (Deliberate technical debt can be ok.)
### Python
* Follow PEP-8 code formatting guidelines - PyCharm will tell you when you violate those guidelines, please watch and resolve.
* 4 space indentation, no tabs
* Ask before adding packages to the project
### Vue/Javascript
* We will use ECMAScript 6
* All control statements which can use brackets should use brackets. It prevents mistakes where developers don't realize their newly added code isn't really part of that if which is missing it's brackets
* else statements go on the next line, not on the same line as the closing bracket
* 2 space indentation, no tabs
* Use camelCase for variables and methods. The only exception is when handling data from the web services which will be underscore_cased.
* We will be using Pug (https://github.com/pugjs/pug) instead of HTML for our markup.
* Use Single File Components for Vue (https://vuejs.org/v2/guide/single-file-components.html)
* In general, the Vue Component object should have, in this order: name, components, mixins, props, data, computed, watch, created, mounted, and methods.
* Ask before adding packages to the project
* We are using Yarn instead of NPM.
### Jira Stories
* When you start work on a story, drag it into In Progress and assign yourself to the story
* Track your hours in that story - we require precision in time spent on Bonaventure for Capital Expenditure Purposes. Please report at a minimum 15 minute increments on your stories.
* Only have 1 story In Progress at any given time (at most 2, but this should be an exception). Complete that story before working on the next.
* If there are questions about a story, ask in the story with a comment.
* In general, stories will have:
    * Why we are implementing this story, what business or technical benefit it will provide (In order to...)
    * Who can perform this requested ability (As a...)
    * What is being requested (I want to...)
    * Definition of Done, or Acceptance Criteria, putting a box around the content and intent and scope of the story
* When a Merge Request is submitted, set the Story as resolved.
    * I'd strongly suggest re-reading the story and ensuring the entire scope and intent of the story is implemented before resolving the story.
    * In general, a BSA should test your changes before moving the story to Verified
    * Once verified, your MR can be merged when approved by one of the Dev Leads (see GitLab)

### Authentication/Authorization
* Consider security for your code.
    * All UIs should prevent route navigation if a user does not have access to that page
    * All Web Services should prevent use of that route if the user does not have permissions to that ability
* This is already baked into the application - use the existing patterns
### User Experience
* In general, server-side pagination/sorting/filtering of table items should be utilized
    * Exceptions can be made for instances that will enhance the User Experience
* Each table/list view should make use of the Personalization Module within Bonaventure
### E2E Testing Automation
* We will utilize Playwright with Python/JavaScript and a version of the Page-Object Model for testing
* Page objects should contain logic related to the structure of each page, not the content
* Playwright Locators should be used by order of preference:
    * Role-based locators (`getByRole`) - most resilient and accessible
    * Text locators (`getByText`, `getByLabel`) - user-facing and readable
    * Test ID (`getByTestId`) - when semantic selectors are insufficient
    * CSS selectors - use sparingly, only when above options are not viable
    * XPath - avoid when possible, use only as last resort
    * Playwright Best Practices: https://playwright.dev/docs/best-practices
* Leverage Playwright's auto-waiting capabilities; avoid manual waits unless absolutely necessary
* Use `expect` assertions with web-first matchers (e.g., `toBeVisible()`, `toHaveText()`) for reliable test assertions
* Brittle selectors/locators are to be avoided; if an element cannot be located with a simple and robust locator, a story can be created to add proper test IDs or ARIA attributes
* Tests should be isolated and independent; each test should set up its own state and clean up afterward
* Tests should not rely on execution order; any test should be able to run independently in any sequence
* In general, assertions should be kept in test functions/classes, not page objects
* Utilize Playwright's built-in features: screenshot on failure, video recording, and trace files for debugging
