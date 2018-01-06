import clashroyale
import os

# Basic functionality
token = os.getenv('crtoken') # get your developer key somehow.

client = clashroyale.Client(token)

profile = client.get_player('#8l9l9gl') # library cleans the tag (strips #)

print(repr(profile))

print(profile.name) 
# Access data via dot notation.

print(profile.stats.favorite_card.name)
# Access API data via snake_case instead of camelCase
# Everything is exactly the same as what is 
# presented in the official API documentation
#
# {
#     "stats": {
#         "favoriteCard": {
#             "name": "P.E.K.K.A"
#         }, 
#        ...
#     },
#    ...
# 

profile.refresh() 
# Refresh model data, This means that the 
# data will be requested again from the api

clan = profile.get_clan() # Request the clan object associated with the profile
print(clan)
print(clan.clan_chest) # dot notation
clan.refresh() # Refresh clan data

member = clan.members[0] # get the member object of the top member
assert member.clan is clan # Keeps a reference to the clan
assert member.rank == 1
# This member object only contains a brief amount of data
full_player = member.get_profile() # member.get_player() is also an alias
# This function requests the full player data using the members tag.

# Getting multiple clans/profiles
clans = client.get_clans('2CCCP', '2U2GGQJ') # indefinite amount of arguments
for clan in clans:
    print(clan.members[0])

filtered = client.get_clan('2cccp', keys=['name', 'tag']) # Filtering with keys= and exclude=
print(filtered.raw_data)

print(client.get_player('2P0LYQ', keys='battles').raw_data.keys()) # battles

print(client.get_auth_stats())
