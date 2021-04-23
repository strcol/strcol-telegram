import hashlib
import json

import requests


class VKAttachment:
    def __init__(self, raw):
        self.raw = raw

    def parse(self):
        data = {}

        if self.raw.get('type') == 'doc':
            data['type'] = 'doc'
            doc = self.raw.get('doc')
            data['url'] = doc['url']
        elif self.raw.get('type') == 'link':
            data['type'] = 'link'
            link = self.raw.get('link')
            data['url'] = link['url']
        elif self.raw.get('type') == 'photo':
            data['type'] = 'photo'
            photo = self.raw.get('photo')
            sizes = photo.get('sizes')
            # find best quality photo available
            resolution = 0
            for size in sizes:
                if size['width'] * size['height'] > resolution:
                    data['url'] = size['url']
                    resolution = size['width'] * size['height']
        elif self.raw.get('type') == 'video':
            data['type'] = 'video'
            video = self.raw.get('video')
            data['url'] = (
                f'https://vk.com/video{video["owner_id"]}_{video["id"]}'
            )
        elif self.raw.get('type') == 'poll':
            data['type'] = 'poll'
            poll = self.raw.get('poll')
            data['url'] = (
                f'https://vk.com/poll{poll["owner_id"]}_{poll["id"]}'
            )

        return data


class VKPost:
    def __init__(self, raw):
        self.raw = raw

    def parse(self):
        data = {}

        data['id'] = self.raw.get('id')
        data['timestamp'] = int(self.raw.get('date') * 1000)
        data['attachments'] = []
        if not self.raw.get('copy_history'):
            # Type 1 = plain text
            data['type'] = 1
            data['text'] = self.raw.get('text')
            if self.raw.get('attachments'):
                for attachment in self.raw.get('attachments'):
                    data['attachments'].append(
                        VKAttachment(attachment).parse()
                    )
        elif self.raw.get('text'):
            # Type 2 = mixed text (plain + shared)
            # Treat them as type 3 until come up with a better solution
            data['type'] = 2
            source = self.raw.get('copy_history')[0]
            data['text'] = source.get('text')
            if source.get('attachments'):
                for attachment in source.get('attachments'):
                    data['attachments'].append(
                        VKAttachment(attachment).parse()
                    )
        else:
            # Type 3 = shared text
            data['type'] = 3
            source = self.raw.get('copy_history')[0]
            data['text'] = source.get('text')
            if source.get('attachments'):
                for attachment in source.get('attachments'):
                    data['attachments'].append(
                        VKAttachment(attachment).parse()
                    )

        # process attachments
        processed_attachments = []
        first = True
        for attachment in data['attachments']:
            if attachment['type'] in ('video', 'poll', 'link'):
                if data['text']:
                    data['text'] += ('\n\n' if first else '\n')
                    data['text'] += attachment['url']
                first = False
            else:
                processed_attachments.append(attachment)
        data['attachments'] = processed_attachments

        data['hash'] = hashlib.md5(
            json.dumps(data).encode()
        ).hexdigest()
        return data


class Client:
    def __init__(self, config):
        self.config = config

    def get_posts(self):
        response = requests.post(
            'https://api.vk.com/method/wall.get',
            data={
                'count': 100,
                'owner_id': self.config.get('VK_SOURCE_ID'),
                'v': self.config.get('VK_API_VERSION'),
                'access_token': self.config.get('VK_API_TOKEN')
            }
        ).json()
        if not response.get('response'):
            return []
        return [
            VKPost(item).parse()
            for item in response['response']['items']
        ]
