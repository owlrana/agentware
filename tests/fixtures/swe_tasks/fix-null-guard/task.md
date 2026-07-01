# Task: Fix Missing Null Guard in User Lookup

The file `users.py` contains a `find_user` function that looks up a user by
email from a list of user dictionaries. It crashes with a `TypeError` when:
1. The `email` argument is `None`
2. Any user dictionary in the list has `None` as its email field

Fix the function so it gracefully handles None values — returning None when
the search email is None, and skipping user entries with None emails.
