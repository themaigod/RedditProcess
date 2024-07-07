"""
load submissions and comments from file
"""
import json
from tqdm import tqdm


global_time_max = None


class LoadRedditObject:
    element_type = "reddit_object"

    def __init__(self, path):
        self.path = path
        self.data = None
        self.load() if self.path else None
        self.objects = {}

    def load(self):
        """
        load the object from json file
        """
        with open(self.path, "r") as f:
            self.data = json.load(f)
        return self.data

    def convert_to_object(self, converter, use_tqdm=False, tqdm_desc=f"convert to object"):
        """
        convert the data to object
        """
        if use_tqdm:
            for idx, item in tqdm(enumerate(self), desc=tqdm_desc, total=len(self)):
                if global_time_max:
                    if item['created_utc'] > global_time_max:
                        continue
                self.objects[idx] = converter(item)
        else:
            for idx, item in enumerate(self):
                if global_time_max:
                    if item['created_utc'] > global_time_max:
                        continue
                self.objects[idx] = converter(item)
        return self.objects

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

    def __setitem__(self, idx, value):
        self.data[idx] = value

    def __iter__(self):
        return iter(self.data)

    def __repr__(self):
        return "{}({})".format(self.element_type, self.path)

    def __str__(self):
        return "{}({})".format(self.element_type, self.path)

    def __contains__(self, item):
        return item in self.data

    def __eq__(self, other):
        return self.data == other.data

    def __ne__(self, other):
        return self.data != other.data

    def __lt__(self, other):
        return len(self.data) < len(other.data)

    def __le__(self, other):
        return len(self.data) <= len(other.data)

    def __gt__(self, other):
        return len(self.data) > len(other.data)

    def __ge__(self, other):
        return len(self.data) >= len(other.data)

    def __add__(self, other):
        return_dict = {}
        return_dict.update(self.data)
        return_dict.update(other.data)
        return return_dict

    def __radd__(self, other):
        return_dict = {}
        return_dict.update(other.data)
        return_dict.update(self.data)
        return return_dict

    def __iadd__(self, other):
        self.data.update(other.data)
        return self


class LoadSubmissions(LoadRedditObject):
    element_type = "submissions"

    def __init__(self, path):
        self.submissions = None
        self.submissions_ids = None
        super().__init__(path)

    def load(self):
        self.submissions = super().load()
        self.submissions_ids = {submission["id"]: idx for idx, submission in enumerate(self.submissions)}
        return self.submissions

    def __len__(self):
        return len(self.submissions)

    def __getitem__(self, idx=None, submission_id=None):
        if idx is None and submission_id is None:
            raise ValueError("idx or submission_id must be specified")
        if idx is None:
            idx = self.submissions_ids[submission_id]
        return self.submissions[idx]

    def __iter__(self):
        return iter(self.submissions)

    def convert_to_object(self, converter, use_tqdm=False, tqdm_desc=f"convert to submission object"):
        """
        convert the data to object
        """
        return super().convert_to_object(converter, use_tqdm, tqdm_desc)


class LoadComments(LoadRedditObject):
    element_type = "comments"

    def __init__(self, path):
        self.comments = None
        self.comments_list = None
        self.comments_ids = None
        self.comments_ids2submission_ids = None
        self.comments_tree = None
        self.objects_dict = {}
        super().__init__(path)

    def load(self):
        self.comments = super().load()
        self.comments_list = [comment for submission_comments in self.comments.values() for comment in
                              submission_comments]
        self.comments_ids = {comment["id"]: idx for idx, comment in enumerate(self.comments_list)}
        self.comments_ids2submission_ids = {comment["id"]: comment["link_id"] for comment in self.comments_list}
        self.comments_tree = {comment["id"]: comment["parent_id"] for comment in self.comments_list}
        return self.comments

    def __len__(self):
        return len(self.comments_list)

    def __getitem__(self, idx=None, comment_id=None):
        if idx is None and comment_id is None:
            raise ValueError("idx or comment_id must be specified")
        if idx is None:
            idx = self.comments_ids[comment_id]
        return self.comments_list[idx]

    def __iter__(self):
        return iter(self.comments_list)

    def convert_to_object(self, converter, use_tqdm=False, tqdm_desc=f"convert to comment object"):
        """
        convert the data to object
        """
        if use_tqdm:
            for idx, item in tqdm(enumerate(self.comments_list), desc=tqdm_desc, total=len(self.comments_list)):
                if global_time_max:
                    if item['created_utc'] > global_time_max:
                        continue
                self.objects[idx] = converter(item)
                item = self.objects[idx]
                if self.comments_ids2submission_ids[item["id_36"]] not in self.objects_dict:
                    self.objects_dict[self.comments_ids2submission_ids[item["id_36"]]] = []
                self.objects_dict[self.comments_ids2submission_ids[item["id_36"]]].append(self.objects[idx])
        else:
            for idx, item in enumerate(self.comments_list):
                if global_time_max:
                    if item['created_utc'] > global_time_max:
                        continue
                self.objects[idx] = converter(item)
                item = self.objects[idx]
                if self.comments_ids2submission_ids[item["id_36"]] not in self.objects_dict:
                    self.objects_dict[self.comments_ids2submission_ids[item["id_36"]]] = []
                self.objects_dict[self.comments_ids2submission_ids[item["id_36"]]].append(self.objects[idx])


if __name__ == "__main__":
    test_submissions = LoadSubmissions("../pushshift.json")
    test_comments = LoadComments("../comments_old.json")
    from reddit_object import objects
    from tqdm import tqdm

    test_submissions_objects = []
    print("creating submission objects")
    for submission in tqdm(test_submissions):
        try:
            test_submissions_objects.append(objects.create_submission(submission))
        except Exception as e:
            print(submission)
            raise e

    test_comments_objects = []
    print("creating comment objects")
    for comment in tqdm(test_comments):
        try:
            test_comments_objects.append(objects.create_comment(comment))
        except Exception as e:
            print(comment)
            raise e
