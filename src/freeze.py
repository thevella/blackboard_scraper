from bbfreeze import Freezer
f = Freezer("blackboard-scraper-1.0", includes=("_strptime",))
f.addScript("scrapergui3edited.py")
f()    # starts the freezing process
