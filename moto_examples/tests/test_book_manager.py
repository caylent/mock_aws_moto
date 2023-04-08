"""Simple test examples"""
import json

import new_book_handler


def test_creating_new_book(main_fixture):
    """Test the creation of a new book, using dynamoDB, S3 and SNS services"""

    author = 'George R. R. Martin'
    title = 'A Song of Ice and Fire'

    lambda_input = json.dumps({
        "attributes": {
            'author': author,
            'title': title,
            'description': 'A good book',
        },
        "file_path": str(main_fixture.data_path/'book_example.pdf')
    })

    new_book_handler.run(lambda_input, context=None)

    main_fixture.assert_dynamo_item(author=author, title=title)
    main_fixture.assert_s3_object(
        key=f'books/{author}/{title}',
        expected_text='This is a book'
    )
    main_fixture.assert_new_book_message_sent(
        expected_message=f'{title} was just published by {author}'
    )


# def test_user_recommendation(main_fixture):
#     """Send a user recommendation email, using dynamoDB and SES"""
#     recommendation = {
#         'user_name': 'Jon Snow',
#         'author': 'Aldous Huxley',
#         'title': 'Brave New World',
#         'emails': ('awesome_reader@caylent.com', )
#     }
#     main_fixture.add_book_to_dynamodb(
#         author=recommendation['author'],
#         title=recommendation['title']
#     )

#     book_manager = BookManager()
#     book_manager.send_user_recommendation(**recommendation)

#     main_fixture.assert_recommendation_email_sent(f'Your friend {recommendation["user_name"]}')
#     main_fixture.assert_recommendation_email_sent(recommendation["author"])
