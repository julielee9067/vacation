import os

import django
from django.conf import settings
from django_slack import slack_message

from isds.exception import print_exception

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "isds.settings")
django.setup()


channel = getattr(settings, "SLACK_VACATION_CHANNEL", None)
try:
    slack_message(
        "core/message.slack",
        {
            "text": "ABC 님이 휴가를 신청하였습니다.",
        },
        channel=channel,
    )
except ValueError:
    print_exception()
