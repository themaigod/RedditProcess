"""
Reddit Objects
"""
from typing import Iterable
import copy

record = {}

prefix_map_id2type = {
    "t1_": "comment",
    "t2_": "redditor",
    "t3_": "submission",
    "t4_": "message",
    "t5_": "subreddit",
    "t6_": "award"}

prefix_map_type2id = {v: k for k, v in prefix_map_id2type.items()}

special_objects = {
    "submission": ["_submission", "_author", "_subreddit", "_comment_tree"],
    "comment": ["_submission", "_author", "_subreddit", "_comment_tree", "_parent"],
    "redditor": [],
    "subreddit": [],
    "comment_tree": ["_head", "_submission"],
    "reddit_object": [],
}

special_attributes = {
    "submission": ["_author_args", "_subreddit_args"],
    "comment": ["_author_args", "_subreddit_args"],
    "redditor": [],
    "subreddit": [],
    "comment_tree": [],
    "reddit_object": [],
}

default_attributes_in_data = {
    "reddit_object": ["id"],
    "submission": ["id", "id_36", "fullname", "body", "title", "selftext", "score", "created_utc", "no_follow",
                   "num_comments", "comments_id", "comments_id_total", "subreddit_id", "subreddit_id_36",
                   "subreddit_fullname"],
    "comment": ["id", "id_36", "fullname", "comments_id", "comments_id_total", "parent_id", "parent_id_36",
                "parent_fullname", "subreddit_id", "subreddit_id_36", "subreddit_fullname"],
    "redditor": ["id", "id_36", "fullname", "activity", "no_follow", "submissions_id", "comments_id"],
    "subreddit": ["id", "id_36", "fullname", "submissions_id", "comments_id"],
    "comment_tree": ["id", "comments_id", "comments_id_total", "submission_id"],
}

default_attributes_values = {
    "reddit_object": {},
    "submission": {"body": "", "title": "", "selftext": "", "score": 0, "created_utc": 0, "no_follow": False,
                   "num_comments": 0, "comments_id": [], "comments_id_total": [], "subreddit_id": None,
                   "subreddit_id_36": None, "subreddit_fullname": None},
    "comment": {"comments_id": [], "comments_id_total": [], "parent_id": None, "parent_id_36": None,
                "parent_fullname": None, "subreddit_id": None, "subreddit_id_36": None, "subreddit_fullname": None},
    "redditor": {"activity": [], "no_follow": [], "submissions_id": [], "comments_id": []},
    "subreddit": {"submissions_id": [], "comments_id": []},
    "comment_tree": {"comments_id": [], "comments_id_total": [], "submission_id": None},
}


class RedditObjectBase:
    object_type = "reddit_object"

    record[object_type] = {}

    def __init__(self, object_dict, use_record=True, enforce_id=False):
        self._data = object_dict

        if "id" not in self._data:
            if enforce_id:
                raise ValueError(f"Object {self.object_type} does not have id")
            print(f"Warning, this {self.object_type} does not have id")

        self.processed = False

        if use_record and "id" in self._data:
            self._record = record[self.object_type]
            try:
                self.process_id()
            except NotImplementedError:
                pass
            if self._data["id"] in self._record:
                self._record[self._data["id"]].get_dict().update(self._data)
                self._data = self._record[self._data["id"]].get_dict()
                self.processed = True
            else:
                self._record[self._data["id"]] = self

    def save(self, depth=0, avoid_attr=False):
        if avoid_attr:
            return {"_data": {"id": self._data["id"]}, "tag": self.object_type}

        data = {"_data": copy.deepcopy(self._data)}
        for attr in special_attributes[self.object_type]:
            data[attr] = getattr(self, attr)
        if depth is None:
            for special_object in special_objects[self.object_type]:
                data[special_object] = getattr(self, special_object).save(depth=None)
        elif depth > 0:
            for special_object in special_objects[self.object_type]:
                data[special_object] = getattr(self, special_object).save(depth=depth - 1)
        data["tag"] = self.object_type
        return data

    @classmethod
    def load(cls, data, depth=0):
        if "id" in data["_data"] and data["_data"]["id"] in record[data["tag"]]:
            obj = record[data["tag"]][data["id"]]
            if len(data["_data"]) > 1:
                obj._data.update(data["_data"])
            if len(data) > 2:
                for attr in special_attributes[obj.object_type]:
                    setattr(obj, attr, data[attr])
                if depth is None:
                    for special_object in special_objects[obj.object_type]:
                        setattr(obj, special_object,
                                getattr(obj, special_object).load(data[special_object], depth=None))
                elif depth > 0:
                    for special_object in special_objects[obj.object_type]:
                        setattr(obj, special_object,
                                getattr(obj, special_object).load(data[special_object], depth=depth - 1))
            obj.processed = True
            return obj
        obj = cls.__new__(cls) if data["tag"] == cls.object_type else RedditObjectBase.__new__(
            CreateObject.object_type2class[data["tag"]])

        obj._data = data["_data"]
        for attr in special_attributes[obj.object_type]:
            setattr(obj, attr, data[attr])
        if depth is None:
            for special_object in special_objects[obj.object_type]:
                setattr(obj, special_object, getattr(obj, special_object).load(data[special_object], depth=None))
        elif depth > 0:
            for special_object in special_objects[obj.object_type]:
                setattr(obj, special_object, getattr(obj, special_object).load(data[special_object], depth=depth - 1))
        obj.processed = True
        obj._record = record[obj.object_type]
        obj._record[obj._data["id"]] = obj
        return obj

    def process_id(self):
        raise NotImplementedError

    def __getattr__(self, item):
        if item in self._data:
            return self._data[item]
        else:
            raise AttributeError(f"{self.object_type} object has no attribute {item}")

    def __getitem__(self, item):
        return self._data[item]

    def __contains__(self, item):
        return item in self._data

    def __dir__(self) -> Iterable[str]:
        """Return an iterable of instance attributes."""
        return list(self._data.keys()) + dir(self.__class__)

    def get_dict(self):
        return self._data

    def __repr__(self):
        return f"<{self.object_type} {self._data['id']}>"

    def __str__(self):
        return f"<{self.object_type} {self._data['id']}>"

    def is_ignore(self):
        if len(self._data) == len(default_attributes_in_data[self.object_type]):
            for attr in default_attributes_values[self.object_type]:
                if self._data[attr] != default_attributes_values[self.object_type][attr]:
                    return False
            return True

        return False


class Submission(RedditObjectBase):
    object_type = "submission"

    record[object_type] = {}

    def __init__(self, submission_dict):
        super().__init__(submission_dict)
        self._submission = self

        if not self.processed:
            # self.process_author_id(self._data["author_fullname"])
            try:
                self._data["author_id"], self._data["author_id_36"], self._data[
                    "author_fullname"] = self.process_author_id(
                    self._data["author_fullname"])
                self._author_args = self.process_author_args()
            except ValueError:
                self._author_args = None
                self._data["author_id"], self._data["author_id_36"], self._data["author_fullname"] = None, None, None
            except KeyError:
                self._author_args = None
                self._data["author_id"], self._data["author_id_36"], self._data["author_fullname"] = None, None, None
        try:
            self._author = create_redditor(self._author_args)

            if not self.processed:
                self._author._data["submissions_id"].append(self._data["id"])
                self._author._data["activity"].append((self._data["created_utc"], self._data["id"], self.object_type))
                self._author._data["activity"].sort(key=lambda x: x[0])
                self._author._data["no_follow"]["submissions"].append(self._data["id"]) \
                    if "no_follow" in self._data and self._data["no_follow"] else None


        except ValueError:
            self._author = None

        except KeyError:
            self._author = None

        except TypeError:
            self._author = None

        if not self.processed:
            try:
                self._data["subreddit_id"], self._data["subreddit_id_36"], self._data[
                    "subreddit_fullname"] = self.process_subreddit_id(
                    self._data["subreddit_id"])
                self._subreddit_args = self.process_subreddit_args()
            except ValueError:
                self._subreddit_args = None
                self._data["subreddit_id"], self._data["subreddit_id_36"], self._data[
                    "subreddit_fullname"] = None, None, None
        try:
            self._subreddit = create_subreddit(self._subreddit_args)
            if not self.processed:
                self._subreddit._data["submissions_id"].append(self._data["id"])
        except ValueError:
            self._subreddit = None

        if not self.processed:

            if not self._data.get("body"):
                self._data["body"] = ""

            if not self._data.get("title"):
                self._data["title"] = ""

            if not self._data.get("selftext"):
                self._data["selftext"] = ""

            if not self._data.get("score"):
                self._data["score"] = 0

            if not self._data.get("created_utc"):
                raise ValueError("Submission must have created_utc")

            if not self._data.get("no_follow"):
                self._data["no_follow"] = False

            if not self._data.get("num_comments"):
                self._data["num_comments"] = 0

            if not self._data.get("comments_id"):
                self._data["comments_id"] = []

            if not self._data.get("comments_total_id"):
                self._data["comments_total_id"] = []

        try:
            self._comment_tree = create_comment_tree({"submission_id": self._data["id"],
                                                      "submission_id_36": self._data["id_36"],
                                                      "submission_fullname": self._data["fullname"],
                                                      "id": self._data["id"],
                                                      "id_36": self._data["id_36"],
                                                      "fullname": self._data["fullname"],
                                                      "comments_id": self._data["comments_id"],
                                                      "comments_total_id": self._data["comments_total_id"]})
        except ValueError:
            self._comment_tree = None

    def process_id(self):
        if self._data.get("id") and isinstance(self._data["id"], str):
            if self._data["id"].startswith(prefix_map_type2id[self.object_type]):
                if not self._data.get("fullname"):
                    self._data["fullname"] = self._data["id"]
                self._data["id_36"] = self._data["id"][3:]
                self._data["id"] = int(self._data["id"][3:], 36)
            else:
                self._data["fullname"] = f"{prefix_map_type2id[self.object_type]}{self._data['id']}"
                self._data["id_36"] = self._data["id"]
                self._data["id"] = int(self._data["id"], 36)
        elif self._data.get("id") and isinstance(self._data["id"], int):
            self._data["id_36"] = int2base(self._data["id"], 36)
            self._data["fullname"] = f"{prefix_map_type2id[self.object_type]}{self._data['id_36']}"

    @staticmethod
    def process_author_id(author_id):
        if isinstance(author_id, str):
            if author_id.startswith(prefix_map_type2id["redditor"]):
                author_id_36 = author_id[3:]
                author_id_int = int(author_id[3:], 36)
                author_fullname = author_id
            else:
                author_id_36 = author_id
                author_id_int = int(author_id, 36)
                author_fullname = f"{prefix_map_type2id['redditor']}{author_id}"
        elif isinstance(author_id, int):
            author_id_36 = int2base(author_id, 36)
            author_id_int = author_id
            author_fullname = f"{prefix_map_type2id['redditor']}{author_id_36}"
        else:
            raise ValueError("author_id must be str or int")

        return author_id_int, author_id_36, author_fullname

    @staticmethod
    def process_subreddit_id(subreddit_id):
        if isinstance(subreddit_id, str):
            if subreddit_id.startswith(prefix_map_type2id["subreddit"]):
                subreddit_id_36 = subreddit_id[3:]
                subreddit_id_int = int(subreddit_id[3:], 36)
                subreddit_fullname = subreddit_id
            else:
                subreddit_id_36 = subreddit_id
                subreddit_id_int = int(subreddit_id, 36)
                subreddit_fullname = f"{prefix_map_type2id['subreddit']}{subreddit_id}"
        elif isinstance(subreddit_id, int):
            subreddit_id_36 = int2base(subreddit_id, 36)
            subreddit_id_int = subreddit_id
            subreddit_fullname = f"{prefix_map_type2id['subreddit']}{subreddit_id_36}"
        else:
            raise ValueError("subreddit_id must be str or int")

        return subreddit_id_int, subreddit_id_36, subreddit_fullname

    def process_author_args(self):
        author_args = {}
        if self._data.get("author"):
            author_args["name"] = self._data["author"]
        if self._data.get("author_fullname"):
            author_args["fullname"] = self._data["author_fullname"]
        if self._data.get("author_id"):
            author_args["id"] = self._data["author_id"]
        if self._data.get("author_id_36"):
            author_args["id_36"] = self._data["author_id_36"]
        if self._data.get("author_flair_text"):
            author_args[f"flair_text_{self._data['id']}"] = self._data["author_flair_text"]
        if self._data.get("author_flair_css_class"):
            author_args[f"flair_css_class_{self._data['id']}"] = self._data["author_flair_css_class"]
        if self._data.get("author_flair_richtext"):
            author_args[f"flair_richtext_{self._data['id']}"] = self._data["author_flair_richtext"]
        if self._data.get("author_flair_template_id"):
            author_args[f"flair_template_id_{self._data['id']}"] = self._data["author_flair_template_id"]
        if self._data.get("author_flair_type"):
            author_args[f"flair_type_{self._data['id']}"] = self._data["author_flair_type"]
        if self._data.get("author_flair_background_color"):
            author_args[f"flair_background_color_{self._data['id']}"] = self._data["author_flair_background_color"]
        if self._data.get("author_flair_text_color"):
            author_args[f"flair_text_color_{self._data['id']}"] = self._data["author_flair_text_color"]
        if self._data.get("author_flair_template_id"):
            author_args[f"flair_template_id_{self._data['id']}"] = self._data["author_flair_template_id"]
        if self._data.get("author_patreon_flair"):
            author_args[f"patreon_flair_{self._data['id']}"] = self._data["author_patreon_flair"]
        if self._data.get("author_premium"):
            author_args[f"premium_{self._data['id']}"] = self._data["author_premium"]
        return author_args

    def process_subreddit_args(self):
        subreddit_args = {}
        if self._data.get("subreddit"):
            subreddit_args["name"] = self._data["subreddit"]
        if self._data.get("subreddit_fullname"):
            subreddit_args["fullname"] = self._data["subreddit_fullname"]
        if self._data.get("subreddit_id"):
            subreddit_args["id"] = self._data["subreddit_id"]
        if self._data.get("subreddit_id_36"):
            subreddit_args["id_36"] = self._data["subreddit_id_36"]
        if self._data.get("subreddit_type"):
            subreddit_args["type"] = self._data["subreddit_type"]
        if self._data.get("subreddit_name_prefixed"):
            subreddit_args["name_prefixed"] = self._data["subreddit_name_prefixed"]
        return subreddit_args

    def is_ignore(self):
        if len(self._data) == len(default_attributes_in_data[self.object_type]):
            for attr in default_attributes_values[self.object_type]:
                if self._data[attr] != default_attributes_values[self.object_type][
                    attr] and attr != "comments_id" and attr != "comments_total_id":
                    return False
            return True
        return False


class Comment(RedditObjectBase):
    object_type = "comment"

    record[object_type] = {}

    def __init__(self, comment_dict):
        super().__init__(comment_dict)
        if not self.processed:
            try:
                if not self._data.get("link_id"):
                    raise ValueError("Comment does not have link_id")

                self._data["link_id"], self._data["link_id_36"], self._data[
                    "link_id_fullname"] = self.process_submission_id(
                    self._data["link_id"]
                )

                if record["submission"].get(self._data["link_id"]):
                    self._submission = record["submission"][self._data["link_id"]]
                else:
                    try:
                        self._submission = create_submission({"id": self._data["link_id"]})
                    except ValueError:
                        self._submission = None

            except ValueError:
                self._submission = None
        else:
            try:
                self._submission = create_submission({"id": self._data["link_id"]})
            except ValueError:
                self._submission = None
            except KeyError:
                self._submission = None

        if not self.processed:
            try:
                self._data["author_id"], self._data["author_id_36"], self._data[
                    "author_fullname"] = self.process_author_id(
                    self._data["author_fullname"],
                )
                self._author_args = self.process_author_args()
            except ValueError:
                self._author_args = None
                self._data["author_id"], self._data["author_id_36"], self._data["author_fullname"] = None, None, None

            except KeyError:
                self._author_args = None
                self._data["author_id"], self._data["author_id_36"], self._data["author_fullname"] = None, None, None

        try:
            self._author = create_redditor(self._author_args)
            if not self.processed:
                self._author._data["comments_id"].append(self._data["id"])
                self._author._data["activity"].append((self._data["created_utc"], self._data["id"], self.object_type))
                self._author._data["activity"].sort(key=lambda x: x[0])
                if self._data.get("no_follow"):
                    self._author._data["no_follow"]['comments'].append(self._data["id"])
        except ValueError:
            self._author = None

        except KeyError:
            self._author = None

        except TypeError:
            self._author = None

        if not self.processed:
            try:
                self._data["subreddit_id"], self._data["subreddit_id_36"], self._data[
                    "subreddit_fullname"] = self.process_subreddit_id(
                    self._data["subreddit"]
                )
                self._subreddit_args = self.process_subreddit_args()
            except ValueError:
                self._subreddit_args = None
                self._data["subreddit_id"], self._data["subreddit_id_36"], self._data[
                    "subreddit_fullname"] = None, None, None

            except KeyError:
                self._subreddit_args = None
                self._data["subreddit_id"], self._data["subreddit_id_36"], self._data[
                    "subreddit_fullname"] = None, None, None

        try:
            self._subreddit = create_subreddit(self._subreddit_args)
            if not self.processed:
                self._subreddit._data["comments_id"].append(self._data["id"])
        except ValueError:
            self._subreddit = None

        except KeyError:
            self._subreddit = None

        except TypeError:
            self._subreddit = None

        if not self.processed:

            try:
                self._data["parent_id"], self._data["parent_id_36"], self._data[
                    "parent_id_fullname"] = self.process_parent_id(
                    self._data["parent_id"]
                )
            except ValueError:
                self._data["parent_id"], self._data["parent_id_36"], self._data[
                    "parent_id_fullname"] = None, None, None

            except KeyError:
                self._data["parent_id"], self._data["parent_id_36"], self._data[
                    "parent_id_fullname"] = None, None, None

            except TypeError:
                self._data["parent_id"], self._data["parent_id_36"], self._data[
                    "parent_id_fullname"] = None, None, None

            if self._submission:
                submission_dict = self._submission.get_dict()
                if not self.processed:
                    submission_dict["comments_total_id"].append(self._data["id"])
                    if not self._data.get("parent_id") or self._data["parent_id"] == self._submission.id:
                        submission_dict["comments_id"].append(self._data["id"])
            #     self._parent = self._submission
            # else:
            #     self._parent = Comment

        # self._parent = self._submission if not self._data.get("parent_id") or self._data[
        #     "parent_id"] == self._submission.id else Comment(self._data["parent_id"])
        if not self._data.get("parent_id") or self._data["parent_id"] == self._submission.id:
            self._parent = self._submission
        else:
            try:
                self._parent = create_comment({"id": self._data["parent_id"]})
                if not self.processed:
                    self._parent._data["comments_id"].append(self._data["id"])
                    self._parent._data["comments_total_id"].append(self._data["id"])
            except ValueError:
                self._parent = None

            except KeyError:
                self._parent = None

        if not self.processed:
            self._data['comments_id'] = []
            self._data['comments_total_id'] = []

        try:
            self._comment_tree = create_comment_tree({
                "id": self._data["id"],
                "id_36": self._data["id_36"],
                "fullname": self._data["fullname"],
                "submission_id": self._data["link_id"],
                "parent_id": self._data["parent_id"],
                "parent_id_36": self._data["parent_id_36"],
                "parent_id_fullname": self._data["parent_id_fullname"],
                "comments_id": self._data["comments_id"],
                "comments_total_id": self._data["comments_total_id"],
            })
        except ValueError:
            self._comment_tree = None

        except KeyError:
            self._comment_tree = None

    @staticmethod
    def process_submission_id(submission_id):
        if isinstance(submission_id, str):
            if submission_id.startswith("t3_"):
                submission_id_36 = submission_id[3:]
                submission_id_int = int(submission_id[3:], 36)
                submission_fullname = submission_id
            else:
                submission_id_36 = submission_id
                submission_id_int = int(submission_id, 36)
                submission_fullname = f"{prefix_map_type2id['submission']}{submission_id}"
        elif isinstance(submission_id, int):
            submission_id_36 = int2base(submission_id, 36)
            submission_id_int = submission_id
            submission_fullname = f"{prefix_map_type2id['submission']}{submission_id_36}"
        else:
            raise ValueError("submission_id must be str or int")

        return submission_id_int, submission_id_36, submission_fullname

    def process_id(self):
        if self._data.get("id") and isinstance(self._data["id"], str):
            if self._data["id"].startswith(prefix_map_type2id[self.object_type]):
                if not self._data.get("fullname"):
                    self._data["fullname"] = self._data["id"]
                self._data["id_36"] = self._data["id"][3:]
                self._data["id"] = int(self._data["id"][3:], 36)
            else:
                self._data["fullname"] = f"{prefix_map_type2id[self.object_type]}{self._data['id']}"
                self._data["id_36"] = self._data["id"]
                self._data["id"] = int(self._data["id"], 36)
        elif self._data.get("id") and isinstance(self._data["id"], int):
            self._data["id_36"] = int2base(self._data["id"], 36)
            self._data["fullname"] = f"{prefix_map_type2id[self.object_type]}{self._data['id_36']}"

        else:
            raise ValueError("id must be str or int")

    @staticmethod
    def process_parent_id(parent_id):
        if isinstance(parent_id, str):
            if parent_id.startswith(prefix_map_type2id["comment"]) or parent_id.startswith(
                    prefix_map_type2id["submission"]):
                parent_id_36 = parent_id[3:]
                parent_id_int = int(parent_id[3:], 36)
                parent_fullname = parent_id
            else:
                parent_id_36 = parent_id
                parent_id_int = int(parent_id, 36)
                parent_fullname = f"{prefix_map_type2id['comment']}{parent_id}"
        elif isinstance(parent_id, int):
            parent_id_36 = int2base(parent_id, 36)
            parent_id_int = parent_id
            parent_fullname = f"{prefix_map_type2id['comment']}{parent_id_36}"
        else:
            raise ValueError("parent_id must be str or int")

        return parent_id_int, parent_id_36, parent_fullname

    @staticmethod
    def process_author_id(author_id):
        if isinstance(author_id, str):
            if author_id.startswith(prefix_map_type2id["redditor"]):
                author_id_36 = author_id[3:]
                author_id_int = int(author_id[3:], 36)
                author_fullname = author_id
            else:
                author_id_36 = author_id
                author_id_int = int(author_id, 36)
                author_fullname = f"{prefix_map_type2id['redditor']}{author_id}"
        elif isinstance(author_id, int):
            author_id_36 = int2base(author_id, 36)
            author_id_int = author_id
            author_fullname = f"{prefix_map_type2id['redditor']}{author_id_36}"
        else:
            raise ValueError("author_id must be str or int")

        return author_id_int, author_id_36, author_fullname

    def process_author_args(self):
        author_args = {}
        if self._data.get("author"):
            author_args["name"] = self._data["author"]
        if self._data.get("author_fullname"):
            author_args["fullname"] = self._data["author_fullname"]
        if self._data.get("author_id"):
            author_args["id"] = self._data["author_id"]
        if self._data.get("author_id_36"):
            author_args["id_36"] = self._data["author_id_36"]
        if self._data.get("author_flair_text"):
            author_args[f"flair_text_{self._data['id']}"] = self._data["author_flair_text"]
        if self._data.get("author_flair_css_class"):
            author_args[f"flair_css_class_{self._data['id']}"] = self._data["author_flair_css_class"]
        if self._data.get("author_flair_richtext"):
            author_args[f"flair_richtext_{self._data['id']}"] = self._data["author_flair_richtext"]
        if self._data.get("author_flair_template_id"):
            author_args[f"flair_template_id_{self._data['id']}"] = self._data["author_flair_template_id"]
        if self._data.get("author_flair_type"):
            author_args[f"flair_type_{self._data['id']}"] = self._data["author_flair_type"]
        if self._data.get("author_flair_background_color"):
            author_args[f"flair_background_color_{self._data['id']}"] = self._data["author_flair_background_color"]
        if self._data.get("author_flair_text_color"):
            author_args[f"flair_text_color_{self._data['id']}"] = self._data["author_flair_text_color"]
        if self._data.get("author_flair_template_id"):
            author_args[f"flair_template_id_{self._data['id']}"] = self._data["author_flair_template_id"]

        if self._data.get("author_patreon_flair"):
            author_args[f"patreon_flair_{self._data['id']}"] = self._data["author_patreon_flair"]
        if self._data.get("author_premium"):
            author_args[f"premium_{self._data['id']}"] = self._data["author_premium"]
        return author_args

    @staticmethod
    def process_subreddit_id(subreddit_id):
        if isinstance(subreddit_id, str):
            if subreddit_id.startswith(prefix_map_type2id["subreddit"]):
                subreddit_id_36 = subreddit_id[3:]
                subreddit_id_int = int(subreddit_id[3:], 36)
                subreddit_fullname = subreddit_id
            else:
                subreddit_id_36 = subreddit_id
                subreddit_id_int = int(subreddit_id, 36)
                subreddit_fullname = f"{prefix_map_type2id['subreddit']}{subreddit_id}"
        elif isinstance(subreddit_id, int):
            subreddit_id_36 = int2base(subreddit_id, 36)
            subreddit_id_int = subreddit_id
            subreddit_fullname = f"{prefix_map_type2id['subreddit']}{subreddit_id_36}"
        else:
            raise ValueError("subreddit_id must be str or int")

        return subreddit_id_int, subreddit_id_36, subreddit_fullname

    def process_subreddit_args(self):
        subreddit_args = {}
        if self._data.get("subreddit"):
            subreddit_args["name"] = self._data["subreddit"]
        if self._data.get("subreddit_fullname"):
            subreddit_args["fullname"] = self._data["subreddit_fullname"]
        if self._data.get("subreddit_id"):
            subreddit_args["id"] = self._data["subreddit_id"]
        if self._data.get("subreddit_id_36"):
            subreddit_args["id_36"] = self._data["subreddit_id_36"]
        if self._data.get("subreddit_type"):
            subreddit_args["type"] = self._data["subreddit_type"]
        if self._data.get("subreddit_name_prefixed"):
            subreddit_args["name_prefixed"] = self._data["subreddit_name_prefixed"]
        return subreddit_args

    def update_parent(self):
        """
        Update parent of comment if it is None or if it is not collected (is_ignore, probably deleted)
        :return:
        """
        if self._parent and self._parent.is_ignore() and self._submission:
            self._parent = self._submission
            self._submission.comments_id.append(self._data["id"])
            self._submission.comments_total_id.append(self._data["id"])

        if not self._parent and self._submission:
            self._parent = self._submission
            self._submission.comments_id.append(self._data["id"])
            self._submission.comments_total_id.append(self._data["id"])

    def is_ignore(self):
        if len(self._data) == len(default_attributes_in_data[self.object_type]):
            for attr in default_attributes_values[self.object_type]:
                if self._data[attr] != default_attributes_values[self.object_type][
                    attr] and attr != "comments_id" and attr != "comments_total_id":
                    return False
            return True

        return False

    def generate_parent_chain(self):
        """
        Generate parent chain for comment
        :return:
        """
        if self._parent and self._parent._data["id"] == self._submission._data["id"]:
            self._data["parent_chain"] = [(self._submission._data["id"], self._submission.object_type)]
        elif self._parent:
            self._parent.generate_parent_chain()
            self._data["parent_chain"] = self._parent._data["parent_chain"] + [
                (self._parent._data["id"], self._parent.object_type)]
        else:
            self._data["parent_chain"] = []

        return self._data["parent_chain"]


class Redditor(RedditObjectBase):
    object_type = "redditor"

    record[object_type] = {}

    def __init__(self, redditor_dict):
        super().__init__(redditor_dict)

        if not self.processed:

            if not self._data.get("comments_id"):
                self._data["comments_id"] = []

            if not self._data.get("submissions_id"):
                self._data["submissions_id"] = []

            if not self._data.get("no_follow"):
                self._data["no_follow"] = {"submissions": [], "comments": []}

            if not self._data.get("activity"):
                self._data["activity"] = []

    def process_id(self):
        if self._data.get("id") and isinstance(self._data["id"], str):
            if self._data["id"].startswith(prefix_map_type2id[self.object_type]):
                if not self._data.get("fullname"):
                    self._data["fullname"] = self._data["id"]
                self._data["id_36"] = self._data["id"][3:]
                self._data["id"] = int(self._data["id"][3:], 36)
            else:
                self._data["fullname"] = f"{prefix_map_type2id[self.object_type]}{self._data['id']}"
                self._data["id_36"] = self._data["id"]
                self._data["id"] = int(self._data["id"], 36)
        elif self._data.get("id") and isinstance(self._data["id"], int):
            self._data["id_36"] = int2base(self._data["id"], 36)
            self._data["fullname"] = f"{prefix_map_type2id[self.object_type]}{self._data['id_36']}"

        else:
            raise ValueError("id must be str or int")


class Subreddit(RedditObjectBase):
    object_type = "subreddit"

    record[object_type] = {}

    def __init__(self, subreddit_dict):
        super().__init__(subreddit_dict)

        if not self.processed:

            if not self._data.get("submissions_id"):
                self._data["submissions_id"] = []

            if not self._data.get("comments_id"):
                self._data["comments_id"] = []

    def process_id(self):
        if self._data.get("id") and isinstance(self._data["id"], str):
            if self._data["id"].startswith(prefix_map_type2id[self.object_type]):
                if not self._data.get("fullname"):
                    self._data["fullname"] = self._data["id"]
                self._data["id_36"] = self._data["id"][3:]
                self._data["id"] = int(self._data["id"][3:], 36)
            else:
                self._data["fullname"] = f"{prefix_map_type2id[self.object_type]}{self._data['id']}"
                self._data["id_36"] = self._data["id"]
                self._data["id"] = int(self._data["id"], 36)
        elif self._data.get("id") and isinstance(self._data["id"], int):
            self._data["id_36"] = int2base(self._data["id"], 36)
            self._data["fullname"] = f"{prefix_map_type2id[self.object_type]}{self._data['id_36']}"

        else:
            raise ValueError("id must be str or int")


class CommentTree(RedditObjectBase):
    object_type = "comment_tree"

    record[object_type] = {}

    def __init__(self, comment_tree_dict):
        super().__init__(comment_tree_dict)
        if not self.processed:
            if not self._data.get("comments_id"):
                if self._data["id"] in record.get("submission") or self._data["id"] == self._data["submission_id"]:
                    try:
                        self._data["comments_id"] = create_submission({"id": self._data["id"]})._data["comments_id"]
                    except ValueError:
                        self._data["comments_id"] = []
                elif self._data["id"] in record.get("comment"):
                    self._data["comments_id"] = record.get("comment")[self._data["id"]]["comments_id"]
                else:
                    self._data["comments_id"] = []
            if not self._data.get("comments_total_id"):
                if self._data["id"] in record.get("submission") or self._data["id"] == self._data["submission_id"]:
                    try:
                        self._data["comments_total_id"] = create_submission({"id": self._data["id"]})._data[
                            "comments_total_id"]
                    except ValueError:
                        self._data["comments_total_id"] = []
                elif self._data["id"] in record.get("comment"):
                    self._data["comments_total_id"] = record.get("comment")[self._data["id"]]["comments_total_id"]
                else:
                    self._data["comments_total_id"] = []

            if not self._data.get("submission_id"):
                if self._data["id"] in record.get("submission_id"):
                    self._data["submission_id"] = record.get("submission_id")[self._data["id"]]
                    try:
                        self._head = create_submission({"id": self._data["submission_id"]})
                    except ValueError:
                        self._head = None
                else:
                    try:
                        self._head = create_comment({"id": self._data["id"]})
                        self._data["submission_id"] = self._head._data["submission_id"]
                    except ValueError:
                        self._head = None
                        self._data["submission_id"] = None

            else:
                if self._data["submission_id"] == self._data["id"]:
                    try:
                        self._head = create_submission({"id": self._data["id"]})
                    except ValueError:
                        self._head = None
                else:
                    try:
                        self._head = create_comment({"id": self._data["id"]})
                    except ValueError:
                        self._head = None

            try:
                self._submission = create_submission({"id": self._data["submission_id"]})
            except ValueError:
                self._submission = None

    def __len__(self):
        return len(self._data["comments_id"])

    def __getitem__(self, index):
        return self._data["comments_id"][index]

    def __iter__(self):
        return iter(self._data["comments_id"])

    def __contains__(self, item):
        return item in self._data["comments_id"]

    def add_comment(self, comment_id):
        self._data["comments_id"].append(comment_id)
        self._data["comments_total_id"].append(comment_id)

    def update_attr(self):
        if not self._head:
            if self._data["id"] in record.get("comment"):
                try:
                    self._head = create_comment({"id": self._data["id"]})
                except ValueError:
                    self._head = None
            elif self._data["id"] in record.get("submission"):
                try:
                    self._head = create_submission({"id": self._data["id"]})
                except ValueError:
                    self._head = None
            else:
                self._head = None
        if not self._submission:
            try:
                self._submission = create_submission({"id": self._data["submission_id"]})
            except ValueError:
                self._submission = None
        if not self._data.get("comments_id"):
            if self._data["id"] in record.get("submission") or self._data["id"] == self._data["submission_id"]:
                try:
                    self._data["comments_id"] = create_submission({"id": self._data["id"]})._data["comments_id"]
                except ValueError:
                    self._data["comments_id"] = []
            elif self._data["id"] in record.get("comment"):
                self._data["comments_id"] = record.get("comment")[self._data["id"]]["comments_id"]
            else:
                self._data["comments_id"] = []
        if not self._data.get("comments_total_id"):
            if self._data["id"] in record.get("submission") or self._data["id"] == self._data["submission_id"]:
                try:
                    self._data["comments_total_id"] = create_submission({"id": self._data["id"]})._data[
                        "comments_total_id"]
                except ValueError:
                    self._data["comments_total_id"] = []
            elif self._data["id"] in record.get("comment"):
                self._data["comments_total_id"] = record.get("comment")[self._data["id"]]["comments_total_id"]
            else:
                self._data["comments_total_id"] = []
        self.update_comments_total_id()

    def update_comments_total_id(self):
        if self._head:
            self._data["comments_total_id"] = self._head._data["comments_total_id"]
        else:
            self._data["comments_total_id"] = []

        comment_total_id = self.dig_depth(self._data["comments_id"], None)

        for comment_id in comment_total_id:
            if comment_id not in self._data["comments_total_id"]:
                self._data["comments_total_id"].append(comment_id)

    @staticmethod
    def dig_depth(comment_id_list, depth=None):
        comment_total_id = []
        for comment_id in comment_id_list:
            try:
                comment = create_comment({"id": comment_id})
                comment_total_id.extend(comment._data["comments_id"])
                if depth:
                    if depth <= 1:
                        pass
                    else:
                        comment_total_id.extend(CommentTree.dig_depth(comment._data["comments_id"], depth - 1))
                else:
                    comment_total_id.extend(CommentTree.dig_depth(comment._data["comments_id"], depth))
            except ValueError:
                pass
        return comment_total_id


class CreateObject:
    object_type2class = {"submission": Submission, "comment": Comment, "redditor": Redditor, "subreddit": Subreddit,
                         "comment_tree": CommentTree}

    @staticmethod
    def create_object(object_dict, object_type="submission"):
        object_id = CreateObject.process_id(object_dict["id"], object_type)
        object_dict["id"] = object_id

        if not CreateObject.if_record(object_id, object_type):
            return CreateObject.object_type2class[object_type](object_dict)
        else:
            required_object = CreateObject.get_record(object_id, object_type)
            required_object.get_dict().update(object_dict)
            return required_object

    @staticmethod
    def process_id(object_id, object_type="submission"):
        if isinstance(object_id, str):
            if object_id.startswith(prefix_map_type2id[object_type]):
                return int(object_id[len(prefix_map_type2id[object_type]):], 36)
            else:
                return int(object_id, 36)
        elif isinstance(object_id, int):
            return object_id
        else:
            raise ValueError(f"Unknown object id type {type(object_id)}")

    @staticmethod
    def if_record(object_id, object_type="submission"):
        if object_type in record:
            if object_id in record[object_type]:
                return True
        return False

    @staticmethod
    def get_record(object_id, object_type="submission"):
        if object_type in record:
            if object_id in record[object_type]:
                return record[object_type][object_id]
        raise ValueError(f"Object {object_id} of type {object_type} not found in record")


# a series of create object functions based on CreateObject class which will not create duplicate objects
# directly create object by ObjectClass(object_dict) will create duplicate objects, which is not allowed
def create_submission(submission_dict):
    return CreateObject.create_object(submission_dict, "submission")


def create_comment(comment_dict):
    return CreateObject.create_object(comment_dict, "comment")


def create_redditor(redditor_dict):
    return CreateObject.create_object(redditor_dict, "redditor")


def create_subreddit(subreddit_dict):
    return CreateObject.create_object(subreddit_dict, "subreddit")


def create_comment_tree(comment_tree_dict):
    return CreateObject.create_object(comment_tree_dict, "comment_tree")


def int2base(x, base=10):
    if base < 2:
        raise ValueError("base must be >= 2")
    elif base > 36:
        result = []
        while x:
            x, r = divmod(x, base)
            result.append(r)
        return result[::-1]
    elif base == 10:
        return str(x)
    elif base == 2:
        return bin(x)
    elif base == 8:
        return oct(x)
    elif base == 16:
        return hex(x)
    else:
        digs = "0123456789abcdefghijklmnopqrstuvwxyz"
        if x < 0:
            sign = -1
        elif x == 0:
            return digs[0]
        else:
            sign = 1
        x *= sign
        digits = []
        while x:
            digits.append(digs[int(x % base)])
            x = int(x / base)
        if sign < 0:
            digits.append("-")
        digits.reverse()
        return "".join(digits)
