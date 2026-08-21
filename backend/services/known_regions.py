"""Curated fallback for province/state lookups.

Open-Meteo's geocoding index (GeoNames-based) frequently has no clean ADM1
(state/province) record for well-known regions - a plain name search for
"Ontario" returns dozens of unrelated small towns rather than the province
itself. For these known regions we resolve to their capital city instead,
scoped to the right country, which gives a sensible single point to fetch
weather for.

Maps a lowercase province/state name -> (capital city, ISO-3166-1 alpha-2
country code).
"""

KNOWN_PROVINCES: dict[str, tuple[str, str]] = {
    # Canadian provinces & territories
    "ontario": ("Toronto", "CA"),
    "quebec": ("Quebec City", "CA"),
    "british columbia": ("Victoria", "CA"),
    "alberta": ("Edmonton", "CA"),
    "manitoba": ("Winnipeg", "CA"),
    "saskatchewan": ("Regina", "CA"),
    "nova scotia": ("Halifax", "CA"),
    "new brunswick": ("Fredericton", "CA"),
    "newfoundland and labrador": ("St. John's", "CA"),
    "prince edward island": ("Charlottetown", "CA"),
    "northwest territories": ("Yellowknife", "CA"),
    "yukon": ("Whitehorse", "CA"),
    "nunavut": ("Iqaluit", "CA"),
    # US states + DC
    "alabama": ("Montgomery", "US"),
    "alaska": ("Juneau", "US"),
    "arizona": ("Phoenix", "US"),
    "arkansas": ("Little Rock", "US"),
    "california": ("Sacramento", "US"),
    "colorado": ("Denver", "US"),
    "connecticut": ("Hartford", "US"),
    "delaware": ("Dover", "US"),
    "florida": ("Tallahassee", "US"),
    "georgia": ("Atlanta", "US"),
    "hawaii": ("Honolulu", "US"),
    "idaho": ("Boise", "US"),
    "illinois": ("Springfield", "US"),
    "indiana": ("Indianapolis", "US"),
    "iowa": ("Des Moines", "US"),
    "kansas": ("Topeka", "US"),
    "kentucky": ("Frankfort", "US"),
    "louisiana": ("Baton Rouge", "US"),
    "maine": ("Augusta", "US"),
    "maryland": ("Annapolis", "US"),
    "massachusetts": ("Boston", "US"),
    "michigan": ("Lansing", "US"),
    "minnesota": ("Saint Paul", "US"),
    "mississippi": ("Jackson", "US"),
    "missouri": ("Jefferson City", "US"),
    "montana": ("Helena", "US"),
    "nebraska": ("Lincoln", "US"),
    "nevada": ("Carson City", "US"),
    "new hampshire": ("Concord", "US"),
    "new jersey": ("Trenton", "US"),
    "new mexico": ("Santa Fe", "US"),
    "new york": ("Albany", "US"),
    "north carolina": ("Raleigh", "US"),
    "north dakota": ("Bismarck", "US"),
    "ohio": ("Columbus", "US"),
    "oklahoma": ("Oklahoma City", "US"),
    "oregon": ("Salem", "US"),
    "pennsylvania": ("Harrisburg", "US"),
    "rhode island": ("Providence", "US"),
    "south carolina": ("Columbia", "US"),
    "south dakota": ("Pierre", "US"),
    "tennessee": ("Nashville", "US"),
    "texas": ("Austin", "US"),
    "utah": ("Salt Lake City", "US"),
    "vermont": ("Montpelier", "US"),
    "virginia": ("Richmond", "US"),
    "washington": ("Olympia", "US"),
    "west virginia": ("Charleston", "US"),
    "wisconsin": ("Madison", "US"),
    "wyoming": ("Cheyenne", "US"),
    "district of columbia": ("Washington", "US"),
}
