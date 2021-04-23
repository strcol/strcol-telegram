import telebot


class TelegramPost:
    def __init__(self, raw):
        self.raw = raw

    def parse(self):
        media = []
        if self.raw['attachments']:
            for attachment in self.raw['attachments']:
                if attachment['type'] == 'photo':
                    media.append(
                        telebot.types.InputMediaPhoto(attachment['url'])
                    )
        text = self.raw['text']

        return {
            'media': media,
            'text': text
        }


class Client:
    def __init__(self, config):
        self.config = config
        self.bot = telebot.TeleBot(self.config.get('TELEGRAM_API_TOKEN'))

    def _make_extendable(self, response):
        if not isinstance(response, list):
            return [response]
        return response

    def publish(self, post):
        response = []
        if post['media']:
            response.extend(self._make_extendable(
                self.bot.send_media_group(
                    self.config.get('TELEGRAM_CHAT_ID'), post['media']
                )
            ))
        if post['text']:
            response.extend(self._make_extendable(
                self.bot.send_message(
                    self.config.get('TELEGRAM_CHAT_ID'), post['text']
                )
            ))
        return response

    def delete(self, id):
        self.bot.delete_message(self.config.get('TELEGRAM_CHAT_ID'), id)
