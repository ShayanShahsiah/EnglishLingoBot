from enum import Enum, auto
from typing import List, Optional, Union, Dict
from abc import ABC, abstractmethod
from telegram import InlineKeyboardMarkup as IKMarkup, InlineKeyboardButton as IKButton, Update, Bot, Message
from time import sleep
class Content():
    """
    Container class for the contents of a Post.

    Attributes:
        text (Optional[str]): String or Bytes to send
        file (Optional[Union[str, bytes]]): file directory or content bytes for multimedia messages.
        type (Content.Type): Type of content (currently TEXT, VOICE, PHOTO).
    """
    class Type(Enum):
        TEXT = auto()
        VOICE = auto()
        PHOTO = auto()

    def __init__(self, text: Optional[str] = None, file: Optional[Union[str, bytes]] = None,
                 type: 'Type' = Type.TEXT):

        self.text = text
        self.file = file
        self.type = type
    def __repr__(self):
        return f"Text: {self.text}, fileType: {type(self.file)}, type: {self.type}"
class Post(ABC):
    """
    Abstract base class for all posts.
    """

    def __init__(self, update: Update, edit = True):
        self.update: Update = update
        self.parse_mode: str = 'html'
        self._update_history()
        self.edit: bool = edit
        self.type: str = self.__class__.__name__
        # specifies if Post should be added to removal list
        self.add_to_removal_list: bool = False
    @abstractmethod
    def _update_history(self):
        pass

    @abstractmethod
    def get_content(self) -> Content:
        pass
    @abstractmethod
    def get_markup(self) -> IKMarkup:
        pass


class post_handler():
    def __init__(self, post: Post, update: Update):
        self.post: Post = post
        self.update: Update = update
    def __repr__(self):
        return f"Post Content: {self.post.get_content()}, Post Markup: {self.post.get_markup()}"
class navigational_post_handler():
    def __init__(self, post: Post, update: Update):
        self._post_stack: List[post_handler] = list()
        self._post_stack.append(post_handler(post, update))
        self._stack_index: int = 0
    def pop(self):
        if self._post_stack:
            self._post_stack.pop()
    def append(self, post: Post, update: Update):
        """
        appends if it doesn't exist already
        """
        if not post in self._post_stack:
            self._post_stack.append(post_handler(post, update))
    def previous(self):
        """
        returns previos, and pops current
        if pop is not desired, use get() instead
        """
        if len(self._post_stack) <= 1:
            return None
        del self._post_stack[-1]
        return self._post_stack[-1]
    def newest(self):
        if self._post_stack:
            return self._post_stack[-1]
        return None
    def get(self, index, delete_proceeding = True):
        """
        delete_proceeding deleted data after index
        """
        if index >= len(self._post_stack) or index <= -(len(self._post_stack)):
            raise IndexError
        if delete_proceeding:
            del self._post_stack[index+1:]
        return self._post_stack[index]
    def get_first(self, type: str, get_first_not = False, delete_proceeding=True):
        """
        get the first instance of type in stack
        get_first_not specifies if it should get first that's NOT type
        delete_proceeding specifies if proceeding datas should be deleted        
        """
        for i in reversed(range(len(self._post_stack))):
            if get_first_not:
                if self._post_stack[i].post.type == type:
                    if delete_proceeding:
                        del self._post_stack[i+1:]
                    return self._post_stack[i]
            else:
                if self._post_stack[i].post.type != type:
                    if delete_proceeding:
                        del self._post_stack[i+1:]
                    return self._post_stack[i]

        return None
    def read_from_db(self):
        raise NotImplementedError
    def write_to_db(self):
        raise NotImplementedError
    def __iter__(self):
        return self
    def __next__(self):
        if self._stack_index == len(self._post_stack):
            self._stack_index = 0
            raise StopIteration
        return self._post_stack[self._stack_index]
        self._stack_index += 1
    def __repr__(self):
        return f"Int: {self._stack_index} , Data: {self._post_stack}"
        
class HistoryHandler():
    def __init__(self):
        self._navigational_post: Dict[str, navigational_post_handler] = dict()
        # posts that are flagged as "to be removed"
        self._removal_messages: List[Message] = list()
        # self.load_from_db()
    def load_from_db(self):
        raise NotImplementedError
    def write_to_db(self):
        raise NotImplementedError
        #other data to save here:
    def clear_posts(self, owner: Update):
        """
        clear previous post data, in case it's not needed
        """
        try:
            owner_id = owner.callback_query.from_user['id']
        except AttributeError:
            return False
        if owner_id in self._navigational_post:
            del self._navigational_post[owner_id]
        return True
    def cleanup(self):
        """
        cleanup empty lists, and possibly superfluous data
        run this periodically
        """
        cleaned = dict()
        for owner_id in self._navigational_post:
            if not self._navigational_post[owner_id]:
                del self._navigational_post[owner_id]
    def add_to_removal_stack(self, message: Message) -> navigational_post_handler:
        """
        add a post to removal stack. The posts will remain here until remove_post is called
        """
        self._removal_messages.append(message)
    def clear_removal_stack(self, bot: Bot, removal_type: str = None):
        """
        remove all posts in removal stack
        optional type specifier to only remove that type: NOT IMPLEMENTED YET
        requires a bot object used to remove the messages
        """
        for message in self._removal_messages:
            print(message.to_dict())
            bot.deleteMessage(message.chat.id, message.message_id)
        self._removal_messages = list()
    def make_navigational_post(self, post: Post, owner: Update)-> navigational_post_handler:
        """
        creates a navigational_post for owner 
        if it already exists, clears it and makes a new one
        """
        self.clear_posts(owner)
        owner_id = owner._effective_user.id
        self._navigational_post[owner_id] = navigational_post_handler(post, owner)
        return self._navigational_post[owner_id]
    def get_navigational_post(self, owner: Update) -> navigational_post_handler:
        """
        parameters:
            owner string specifies who the post belongs to, use something consistent like update.callback_query.from_user['id']
        return:
            list of navigational_post_handlers for owner.
            creates a list if it doesn't exist already
        """
        owner_id = owner._effective_user.id
        if not owner_id in self._navigational_post:
            return None
        return self._navigational_post[owner_id]
    def __repr__(self):
        res = "Nav Posts\n"
        for owner_id in self._navigational_post:
            res += f"Owner: {owner_id} Data: {self._navigational_post[owner_id]}"
        res += "\nRemoval Posts\n"
        for removal in self._removal_messages:
            res += str(removal) + '\n'
        return res
if __name__ == "__main__":
    a = IKMarkup([[IKButton('بازگشت', callback_data="Callback.BACK")]])
    for one in a.to_dict()["inline_keyboard"]:
        for sub in one:
            print(sub['text'])
a = {
    'update_id': 128053597, 
    'message': {'message_id': 603, 'date': 1583514771, 'chat': {'id': 714124313, 'type': 'private', 'username': 'Dorenas', 'first_name': 'MDorßa'}, 'text': '/houses', 'entities': [{'type': 'bot_command', 'offset': 0, 'length': 7}], 'caption_entities': [], 'photo': [], 'new_chat_members': [], 'new_chat_photo': [], 'delete_chat_photo': False, 'group_chat_created': False, 'supergroup_chat_created': False, 'channel_chat_created': False, 'from': {'id': 714124313, 'first_name': 'MDorßa', 'is_bot': False, 'username': 'Dorenas', 'language_code': 'fa'}}, 
    '_effective_user': {'id': 714124313, 'first_name': 'MDorßa', 'is_bot': False, 'username': 'Dorenas', 'language_code': 'fa'}, 
    '_effective_chat': {'id': 714124313, 'type': 'private', 'username': 'Dorenas', 'first_name': 'MDorßa'}, 
    '_effective_message': {'message_id': 603, 'date': 1583514771, 'chat': {'id': 714124313, 'type': 'private', 'username': 'Dorenas', 'first_name': 'MDorßa'}, 'text': '/houses', 'entities': [{'type': 'bot_command', 'offset': 0, 'length': 7}], 'caption_entities': [], 'photo': [], 'new_chat_members': [], 'new_chat_photo': [], 'delete_chat_photo': False, 'group_chat_created': False, 'supergroup_chat_created': False, 'channel_chat_created': False, 'from': {'id': 714124313, 'first_name': 'MDorßa', 'is_bot': False, 'username': 'Dorenas', 'language_code': 'fa'}}
    }
b = {
    'message_id': 608, 
    'date': 1583515000, 
    'chat': {'id': 714124313, 'type': 'private', 'username': 'Dorenas', 'first_name': 'MDorßa'}, 
    'entities': [], 
    'caption_entities': [{'type': 'bold', 'offset': 0, 'length': 5}], 
    'photo': [], 
    'voice': {'file_id': 'AwACAgQAAxkDAAICYF5ihXilJNUSnJeIFD87jl6hAAH9ggAC_QYAAg29GVOJpFCtaJtRWhgE', 'duration': 0, 'mime_type': 'audio/ogg', 'file_size': 12000}, 
    'caption': 'house\nمنزل\nچهاردیواری\nجا دادن\nمنزل گزیدن\nمسکن\nمنزل دادن\nمنزلگاه\nمسکن دادن\nخاندان\nخانه\nسرای\nچاردیواری', 
    'new_chat_members': [], 
    'new_chat_photo': [], 
    'delete_chat_photo': False, 
    'group_chat_created': False, 
    'supergroup_chat_created': False, 
    'channel_chat_created': False, 
    'reply_markup': {'inline_keyboard': [[{'text': 'بستن', 'callback_data': 'MESSAGE_CLEANUP'}]]}, 
    'from': {'id': 938237304, 
    'first_name': 'Facts Bot', 
    'is_bot': True, 
    'username': 'TebTibBot'}}