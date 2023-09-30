The parser collects hotel data from the specified countries from booking.com from all pages and puts it into excel

Usage\
list of countries to spar\
countries = ["dubai"]\
pars_hotels(countries)

Parameters\
limit - minimum hotel price (integer type)\
currency - currency (string type)

Example\
countries = ["dubai"] #enter countries\
pars_hotels(countries, limit=100, currency="usd") #look for hotels in dubai that cost 100 doollars or more.
