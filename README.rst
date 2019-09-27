Punter
======

Library in charge of gathering and cleaning up data related to Prismata (strategy game).

Install as library
--------------------

    **pip install punter**

Development environment
-----------------------

0. Virtual environment (look at virtualenvwrapper):

   Create:

    mkvirtualenv punter

   Activate:

    workon punter

1. Install dependencies:

    pip install -r requirements-dev.txt

2. Run tests:

    ./runtests.sh

3. Run linters:

    ./runlinters.sh

Sample uses:
------------

* Fetch all units data from the source site and save all sources:

    fetch_units(save_source=True)

* Fetch only specific units:

    fetch_units(include=["Drone", "Engineer"])

* Fetch information from local files instead of source site:

    Change punter.scrape.wiki.PRISMATA_WIKI["BASE_URL"] to the path to source files (by default files are saved to punter.scrape.wiki.PRISMATA_WIKI["SAVE_PATH"])

    fetch_units()

* Once you fetch units, you can export the result to:

    JSON: export_units_json(result)

    CSV: export_units_csv(result)
