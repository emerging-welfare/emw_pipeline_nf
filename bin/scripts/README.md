# Steps of our geocoding algorithm
In construct_event_database script, each document has some amount of predicted clusters (clusters of positive sentences, each cluster being a candidate for an event), and these clusters are geocoded using the logical flow below.

1. Check if the document has an html place
   + If the document does not have an html place -> html_place is empty and html_place_status is "No Html Place". **Go to step 2**.
   + Else, if the document has an html place
       + If the html place is in our foreign place dictionary (countries and their capitals) -> html_place_status is "Foreign Html Place". **Discard whole document** (We assume that this article is from an irrelevant country).
       + Else If the html place is in our ignore list (consists of "India", words like "the", "a", "then" etc.) -> html_place_status is "Ignore List Fail". **Go to step 2**.
       + Else If the html place is in our state name dictionary -> html_place_status is "State Name Fail". **Go to step 2**.
       + Else If the html place is in our district dictionary -> html_place_status is "Success". **All of the clusters are events** and take this district name regardless of their extracted places! (Each cluster has a geocoding_status of "Success from Html")
       + Else If the html place is considered a place in India by geopy -> html_place_status is "Geopy Success". **All of the clusters are events** and take this place name regardless of their extracted places! (Each cluster has a geocoding_status of "Success from Html")
       + Else, none of the above happened -> html_place_status is "Not Found Fail". **Go to step 2**.
2. For each cluster (possible event):
    1. Get all the extracted places and order them from most common to least common
    2. If any of the extracted place names is in our foreign dictionary -> **discard this cluster**. It geocoding_status will be "Foreign Place Fail".
    3. Go over each of them until:
        + If a place name is in our district dictionary -> **Cluster is an event**. Its geocoding_status is "Success".
        + Else if a place name is considered a place in India by geopy -> **Cluster is an event**. Its geocoding_status is "Geopy Success".
    4. If none of the place names was a success, then we check if we can find any state names.
        + If html place is in our state dictionary -> **Cluster is an event?** (Not wholly true yet since we don't assign any coordinates to this event). Its geocoding_status is "Only State Name from Html"
        + Else If any one of the extracted places is in our state dictionary -> **Cluster is an event?** (Not wholly true yet since we don't assign any coordinates to this event). Its geocoding_status is "Only State Name"
    5. If none of the place names was a state name -> **Cluster is not an event**. Its geocoding_status is "No Name Fail"
