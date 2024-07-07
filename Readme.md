# Repository for further processing Reddits data

## Introduction

In some third party packages for Twitter, they can provide the objects for different kinds of data,such as user, tweet,
etc. and provide the link to other objects. More importantly, they can build the tree of conversation for the tweets.
That makes it easy to analyze the data, especially as graph data. However, in Reddit, the only thing we can get is the
dicts of single post, and for different kinds of posts, the keys in the dict are different. So, it is hard to analyze
the data. Here, we provide a repository to process the data from Reddit, build objects for different kinds of data, and
build the tree of conversation for the comments.

## Data preparation

The original data you have downloaded is a series of zst files. We recommend you to get the data you need by using
PushshiftDumps. The processing after PushshiftDumps is to extract the data from the zst files and save them as json
files.

Here we provide a script to extract the data from the zst files and save them as json files. You can run the script by

```bash
python zst2json.py --zst_file INPUT_ZST_FILE --output_file OUTPUT_JSON_FILE
```

where `INPUT_ZST_FILE` is the path of the zst file and `OUTPUT_JSON_FILE` is the path to save the json file. Please 
preinstall `zstandard` package first.

## Data processing

For json files (seperated by submission and comment), we provide a script to load the data from the json files and build
objects we want. You can do it in your code by

```python
import data_processer

reddit_data = data_processer.DataProcesserReddit(submisson_file=SUBMISSION_JSON_FILE, comment_file=COMMENT_JSON_FILE)
```

where `SUBMISSION_JSON_FILE` is the path of the submission json file and `COMMENT_JSON_FILE` is the path of the comment
json

You can get the objects by

```python
reddit_data.submission_objects
reddit_data.comment_objects
reddit_data.comment_tree_objects
reddit_data.subreddit_objects
reddit_data.redditor_objects
```

where `submission_objects` is a list of submission objects, `comment_objects` is a list of comment objects,
`comment_tree_objects` is a list of comment tree objects, `subreddit_objects` is a list of subreddit objects, and
`redditor_objects` is a list of redditor objects.

## Data objects

### Submission object

It has unique keys:

- `id`: the id of the submission
- `id_36`: the id of the submission in base 36

`id_36` is widely used in Reddit, and some situations may use `id` to identify the submission while some situations may
use
`id_36`. So, we provide both of them.

We keep all the keys shown in the original dict in the submission object, you can check the keys in the code. We add
two keys to quickly access
the direct comments and the all comments of the submission.

```python
submission_object.comments_id
submission_object.comments_total_id
```

We also provide the links to its author, subreddit, and comment_tree.

```python
submission_object._author
submission_object._subreddit
submission_object._comment_tree
```

### Comment object

The unique keys are still kept.

For the submission it belongs to, we provide the keys to the submission id.

```python
link_id
link_id_36
```

We also provide the links to its author, subreddit, submission, comment_tree and parent comment.

```python
comment_object._author
comment_object._subreddit
comment_object._parent
comment_object._submission
comment_object._comment_tree
```

### Redditor object

The unique keys are still kept.

We provide the ids to its submissions and comments.

```python
redditor_object.submissions_id
redditor_object.comments_id
```

We also provide the timeline of the redditor.

```python
redditor_object.activity
```

Each item in the timeline is a tuple of the time, id, and type of the object (submission or comment).

### Subreddit object

The unique keys are still kept.

We provide the ids to its submissions and comments.

```python
subreddit_object.submissions_id
subreddit_object.comments_id
```

### Comment tree object

Only `id` is unique which is the id of the root submission or comment.

This is the object that always maintains the tree structure of the comments.

```python
comment_tree_object.comments_id
comment_tree_object.comments_total_id
comment_tree_object._head  # link to the head submission
```

## Something behind this repository

Actually, in the beginning of the project, I underestimated the difficulty of the project. There are so many kinds of
situations in the data, and the only way is to find examples if it will have this key or not. For the tree of
conversation, it may lack some comments, because some people may delete their comments. As a result, when you look
at `objects.py`, you could find more one thousand lines of code to generate the objects properly. Hopefully under this
repository, it can save your time to process the data from Reddit.
