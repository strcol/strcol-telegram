import time

import api.telegram
import api.vk
import default.config
import storage.database
import utils.config


def main():
    config = utils.config.Config(
        'config.json',
        default=default.config.DEFAULT
    )
    database = storage.database.MongoDatabase(config.get('DATABASE_HOST'))
    vk = api.vk.Client(config)
    telegram = api.telegram.Client(config)

    while True:
        # retrieve most recent 100 posts from VK
        posts = vk.get_posts()
        # open connection to mongo
        connection = database.connect()[config.get('DATABASE_NAME')]

        delay = config.get('LEGACY_MAX_DELAY')
        timestamp = int(time.time() * 1000)
        posts_id = [post['id'] for post in posts]
        for post in posts:
            data = connection.posts.find_one({
                'id': post['id']
            })
            if not data:
                if delay and post['timestamp'] + delay * 1000 < timestamp:
                    connection.posts.insert_one({
                        'id': post['id'],
                        'fingerprint': post['hash'],
                        'published': False,
                        'reason': 'LEGACY_MAX_DELAY_EXPIRED'
                    })
                    continue
                result = telegram.publish(
                    api.telegram.TelegramPost(post).parse()
                )
                connection.posts.insert_one({
                    'id': post['id'],
                    'fingerprint': post['hash'],
                    'published': True,
                    'posts': [_post.message_id for _post in result]
                })
                # send no more than one msg per second in order to avoid 429
                time.sleep(len(result))
            elif data['published'] and data['fingerprint'] != post['hash']:
                # TODO update post
                pass
        for post in connection.posts.find({}):
            # delete post if it was deleted from source
            if post['id'] not in posts_id and post['id'] > min(posts_id):
                for _post in post['posts']:
                    telegram.delete(_post)
                connection.posts.update_one({
                    'id': post['id']
                }, {
                    '$set': {
                        'published': False,
                        'reason': 'DELETED_FROM_SOURCE'
                    }
                })

        time.sleep(config.get('REFRESH_INTERVAL'))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Exiting..')
