"""Simple test examples"""
import json

import user_recommendation_handler


def test_user_recommendation(main_fixture):
    """Send a user recommendation email, using dynamoDB and SES"""
    recommendation = {
        'user_name': 'Jon Snow',
        'author': 'Aldous Huxley',
        'title': 'Brave New World',
        'emails': ('awesome_reader@caylent.com', )
    }
    main_fixture.add_book_to_dynamodb(
        author=recommendation['author'],
        title=recommendation['title']
    )

    user_recommendation_handler.run(json.dumps(recommendation),  context=None)

    main_fixture.assert_recommendation_email_sent(f'Your friend {recommendation["user_name"]}')
    main_fixture.assert_recommendation_email_sent(recommendation["author"])
