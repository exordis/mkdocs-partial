import requests


def test_tg():
    message = r"""
🔥 ***\<no severity\> Alert Summary text***
[Source](https://prometheus-dev.example.com)
🏷commonlabelkey1: `commonlabelvalue1`
🏷commonlabelkey2: `commonlabelvalue2`
🏷instance: `some-instance01:1234`
🏷job: `some-job`
🏷label2: `value2`
🏷manyletters: `long_long_text_to_test_how_it_looks_like_in_the_alert_message_foo_bar_baz`

✅ ***\<ritical\> Alert Summary text***
_Detailed alert\+ description text\. \> john doe jane doe some veeery long text needed_
[Source](https://prometheus-dev.example.com) [Runbook](http://runbook)
🏷commonlabelkey1: `commonlabelvalue1`
🏷commonlabelkey2: `commonlabelvalue2`
🏷instance: `some-instance02:1234`
🏷job: `some-job`
🏷label2: `value2`
🏷manyletters: `long_long_text_to_test_how_it_looks_like_in_the_alert_message_foo_bar_baz`
\#alerts
"""

    url = "https://api.telegram.org/bot7529571698%3AAAHfPgPZGtxKP_5JRkuyctaO6XNr-SL8iy0/sendMessage"

    payload = {
        "text": message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
        "disable_notification": False,
        "reply_to_message_id": None,
        "chat_id": "-1002189220838",
    }
    headers = {
        "accept": "application/json",
        "User-Agent": "Telegram Bot SDK - (https://github.com/irazasyed/telegram-bot-sdk)",
        "content-type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text)
