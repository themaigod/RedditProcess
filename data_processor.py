"""
data processing for reddit
"""

from tqdm import tqdm

from .load import LoadSubmissions, LoadComments
from . import objects
from typing import List, Dict, Any, Optional


def access_attribute(obj: object, attributes: List[str]) -> Optional[Any]:
    """
    access attribute of an object by a list of attributes (strings) in order (from outer to inner) and return the value
    for example, access_attribute(obj, ["_author", "id"]) is equivalent to obj._author.id
    It is to avoid if the value of one of the attributes is None, the program will crash. It will return None instead.
    :param obj: an object
    :param attributes: a list of attributes (strings) in order (from outer to inner)
    :return: the value of the attribute
    """
    for attribute in attributes:
        obj = getattr(obj, attribute, None)
        if obj is None:
            return None
    return obj


def load_data_from_file(submission_file: str, comment_file: str) -> (LoadSubmissions, LoadComments):
    """
    load data from file
    """
    submissions = LoadSubmissions(submission_file)
    comments = LoadComments(comment_file)
    return submissions, comments


def generate_data_objects(submissions: LoadSubmissions, comments: LoadComments) -> Dict[str, objects.RedditObjectBase]:
    """
    generate data objects
    """
    submissions.convert_to_object(objects.create_submission, use_tqdm=True)
    comments.convert_to_object(objects.create_comment, use_tqdm=True)

    for comment in tqdm(objects.record["comment"].values(), desc="repairing comment",
                        total=len(objects.record["comment"])):
        comment.update_parent()
    for comment_tree in tqdm(objects.record["comment_tree"].values(), desc="repairing comment tree",
                             total=len(objects.record["comment_tree"])):
        comment_tree.update_attr()
    return objects.record


class DataProcessor:
    """
    data processor
    """

    def __init__(self, **kwargs):
        self.data = self.load_data_from_file(**kwargs)
        self.objects = self.generate_data_objects()
        self.generator = self.construct_generator()

    def __getitem__(self, item):
        return self.generator[item]

    def __len__(self):
        return len(self.generator)

    def __iter__(self):
        return iter(self.generator)

    def load_data_from_file(self, **kwargs) -> Optional[Any]:
        """
        load data from file
        """
        raise NotImplementedError

    def generate_data_objects(self) -> Optional[Any]:
        """
        generate data objects
        """
        raise NotImplementedError

    def construct_generator(self) -> Optional[Any]:
        """
        construct generator
        """
        raise NotImplementedError


class DataProcessorReddit(DataProcessor):
    """
    data processor for reddit
    """

    def __init__(self, submission_file: str = None, comment_file: str = None, return_type: str = "submission"):
        """
        :param submission_file: submission file path
        :param comment_file: comment file path
        :param return_type: return type (submission, comment, comment_tree, redditor, subreddit) (default: submission)
        for __getitem__
        """
        self.submissions = None
        self.comments = None
        self.submission_objects = None
        self.comment_objects = None
        self.comment_tree_objects = None
        self.redditor_objects = None
        self.subreddit_objects = None
        self.return_type = return_type
        super().__init__(submission_file=submission_file, comment_file=comment_file)

    def load_data_from_file(self, **kwargs) -> (LoadSubmissions, LoadComments):
        """
        load data from file
        """

        self.submissions, self.comments = load_data_from_file(kwargs["submission_file"], kwargs["comment_file"])
        return {"submissions": self.submissions, "comments": self.comments}

    def generate_data_objects(self) -> Dict[str, objects.RedditObjectBase]:
        """
        generate data objects
        """
        record = generate_data_objects(self.submissions, self.comments)
        self.submission_objects = record["submission"]
        self.comment_objects = record["comment"]
        self.comment_tree_objects = record["comment_tree"]
        self.redditor_objects = record["redditor"]
        self.subreddit_objects = record["subreddit"]
        return record

    def construct_generator(self) -> Dict[str, List[objects.RedditObjectBase]]:
        """
        construct generator
        """
        return self.objects

    def __getitem__(self, item):
        return self.generator[self.return_type][item]

    def __len__(self):
        return len(self.generator[self.return_type])

    def __iter__(self):
        return iter(self.generator[self.return_type])
