"""Simple test examples"""


from book_manager import BookManager


def test_creating_new_book(main_fixture):
    """Create a new book, using dynamoDB, S3 and SNS services"""

    author = 'George R. R. Martin'
    title = 'A Song of Ice and Fire'

    book_attributes = {
        'Author': author,
        'Title': title,
        'Description': 'A good book',
    }

    book_manager = BookManager()
    book_manager.create_new_book(book_attributes, main_fixture.data_path/'book_example.pdf')

    main_fixture.assert_dynamo_item(author=author, title=title)

    main_fixture.assert_s3_object(
        key='books/George R. R. Martin/A Song of Ice and Fire',
        expected_text='This is a book'
    )

    main_fixture.assert_new_book_message_sent(
        expected_message=f'{title} was just published by {author}'
    )


def test_user_recommendation(main_fixture):
    """Send a user recommendation email, using dynamoDB and SES"""
    recommendation = {
        'user_name': 'Jon Snow',
        'author': 'Aldous Huxley',
        'title': 'Brave New World',
        'emails': ('awesome_reader@caylent.com', )
    }
    main_fixture.add_book(author=recommendation['author'], title=recommendation['title'])

    book_manager = BookManager()
    book_manager.send_user_recommendation(**recommendation)
    # TODO: Add an assert here
