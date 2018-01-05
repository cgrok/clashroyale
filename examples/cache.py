import clashroyale
import os

c = clashroyale.Client(
    token=os.getenv('crtoken'),
    cache_fp='cache.db',
    cache_expires=10 # Seconds before client should request from api again.
    )

for _ in range(100):
    model = c.get_top_clans()
    print(model, 
          model.cached, # Bool indicating whether or not the data is cached.
          model.last_updated) # Datetime for the time the data was last updated from the API.

# Finished very quickly due to caching!
