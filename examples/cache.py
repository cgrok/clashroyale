import clashroyale
import os

c = clashroyale.Client(
    token=os.getenv('crtoken'),
    cache_fp='cache.db',
    cache_expires=10
    )

for x in range(100):
    print(c.get_top_clans())

# Finished very quickly due to caching!