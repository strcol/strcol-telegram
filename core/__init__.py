import time
import traceback

import core.api.telegram
import core.api.vk
import core.database
import core.logger
import config


def tick(database, vk, telegram):
    # retrieve most recent 100 posts from VK
    posts = vk.get_posts()
    core.logger.LOGGER_INSTANCE.info(
        f'Retrieved {len(posts)} posts from VK'
    )

    delay = config.LEGACY_MAX_DELAY
    timestamp = int(time.time() * 1000)
    posts_id = [post['id'] for post in posts]
    for post in posts:
        data = database.session.posts.find_one({
            'id': post['id']
        })
        if not data:
            if delay and post['timestamp'] + delay * 1000 < timestamp:
                core.logger.LOGGER_INSTANCE.info(
                    f'Post {post["id"]} not published: '
                    f'LEGACY_MAX_DELAY_EXPIRED'
                )
                database.session.posts.insert_one({
                    'id': post['id'],
                    'fingerprint': post['hash'],
                    'published': False,
                    'reason': 'LEGACY_MAX_DELAY_EXPIRED'
                })
                continue
            result = telegram.publish(
                api.telegram.TelegramPost(post).parse()
            )
            core.logger.LOGGER_INSTANCE.info(
                f'Post {post["id"]} published: {result}'
            )
            database.session.posts.insert_one({
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
    for post in database.session.posts.find({}):
        # delete post if it was deleted from source
        if post['id'] not in posts_id and post['id'] > min(posts_id):
            for _post in post['posts']:
                telegram.delete(_post)
            core.logger.LOGGER_INSTANCE.info(
                f'Post {post["id"]} deleted: DELETED_FROM_SOURCE'
            )
            database.session.posts.update_one({
                'id': post['id']
            }, {
                '$set': {
                    'published': False,
                    'reason': 'DELETED_FROM_SOURCE'
                }
            })


def report_error(database, error):
    try:
        core.logger.LOGGER_INSTANCE.error(error)
        database.session.errors.insert_one({
            'timestamp': int(time.time() * 1000),
            'error': error
        })
    except Exception:
        pass


def create_app():
    logger = core.logger.Logger(
        level=config.LOGGER_LEVEL, file=config.LOGGER_FILE
    )

    logger.info('Initializing database...')
    database = core.database.Database(
        host=config.DATABASE_HOST,
        name=config.DATABASE_NAME,
        logger_debug=logger.debug,
        logger_info=logger.info,
        logger_warning=logger.warning,
        logger_error=logger.error
    )
    database.connect()
    service = core.database.KeepAliveService(database)
    service.start()
    service.wait_for_connection()

    vk = api.vk.Client()
    telegram = api.telegram.Client()

    while True:
        try:
            tick(database, vk, telegram)
        except Exception:
            report_error(database, traceback.format_exc())
        time.sleep(config.REFRESH_INTERVAL)
