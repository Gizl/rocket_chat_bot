from pprint import pprint
from rocketchat_API.rocketchat import RocketChat

import settings

rocket = RocketChat(settings.ROCKET_USERNAME, settings.ROCKET_PASSWORD, server_url=settings.ROCKET_URL)
# pprint(rocket.me().json())
pprint(rocket.channels_list().json())
