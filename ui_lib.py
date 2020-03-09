from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Optional, Callable, Union
import ast

from telegram import InlineKeyboardMarkup as IKMarkup, InlineKeyboardButton as IKButton, Update

import global_vars

class Callback():
    BACK = 'BACK'
    NEXT = 'PAGE_CONTAINER_NEXT'
    PREVIOUS = 'PAGE_CONTAINER_PREVIOUS'
    MESSAGE_CLEANUP = 'MESSAGE_CLEANUP'


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
        # TODO: Files shouldn't be saved statically, might use too much space. save to file and send over time in another process instead
        self.file = file
        self.type = type

    def __repr__(self):
        safetext = self.text[:30].replace('\n', ' ') + '...'
        return f"\n\t\tText: {safetext}\n\t\tfileType: {type(self.file)}\n\t\ttype: {self.type}"


class Post(ABC):
    """
    Abstract base class for all posts.
    """

    def __init__(self, update: Update):
        self.owner_id = update._effective_user.id
        self.chat_id = update._effective_chat.id
        # this is not the message id for this post, only current message
        self._message_id = update._effective_message.message_id
        self.parse_mode: str = 'html'
        self.edit: bool = True
        self.type: str = self.__class__.__name__
        self.add_to_removal_stack = False
        self.add_to_navigational_stack = True

    def _update_history(self):
        # append to history or removal stack
        if self.add_to_navigational_stack:
            global_vars.history.make_navigational_post(self.owner_id)
            global_vars.history.add_navigational_post(self, self.owner_id)
        if self.add_to_removal_stack:
            # add to-be message(AKA this post) to removal stack(offset 1)
            global_vars.history.add_to_removal_stack_lite(
                self.owner_id, self.chat_id, self._message_id, 1)

    @abstractmethod
    def get_content(self) -> Content:
        """
        Method MUST return the SAME copy of the Content object each time
        Be sure to initiate any randomness in the __init__ function of the class, before returning it from here
        """
        pass

    @abstractmethod
    def get_markup(self) -> IKMarkup:
        pass


class BasicPost(Post):
    """
    Abstract base class for posts that don't support navigation to the previous post.
    """

    def __init__(self, update: Update):
        super().__init__(update)
        self._update_history()


class BackSupportPost(Post):
    """
    Abstract base class for posts that support navigation to the previous post.
    """
    def __init__(self, update: Update):
        super().__init__(update)
        self._update_history()

    def go_back(self) -> Post:
        return global_vars.history.get_navigational_post(self.owner_id).previous().post

    def get_markup(self) -> IKMarkup:
        return IKMarkup([[IKButton('بازگشت', callback_data=Callback.BACK)]])


class GhostPost(Post):
    """
    Abstract base class for posts that are outside the back navigation stack.

    Could for example be used for a short message sent after a bigger "main" message
    without affecting the "back button" functionality of the older message.

    Messages using this class can clump up and decrease visability, so a special markup is used to remove them
    """

    def __init__(self, update: Update):
        super().__init__(update)
        # Doesn't affect the global navigation stack
        self.add_to_navigational_stack = False
        # Does affect cleanup stack(if specified in self.add_to_removal_list)
        self.add_to_removal_stack = True
        self.edit = False
        self._update_history()

    def get_markup(self) -> IKMarkup:
        return IKMarkup([[IKButton('بستن', callback_data=Callback.MESSAGE_CLEANUP)]])


class PageContainerPost(Post):
    """
    Abstract base class for posts that support navigation between several "pages". 
    """

    def __init__(self, update: Update, num_pages):
        super().__init__(update)
        self.num_pages = num_pages
        self.page_idx = 0
        self._update_history()
        # don't override previous post, should be able to return to it
        # global_vars.history.make_navigational_post(self, self.update)

    def go_back(self) -> Post:
        return global_vars.history.get_navigational_post(self.owner_id).previous().post

    def next_page(self):
        self.page_idx += 1
        
    def previous_page(self):
        self.page_idx -= 1

    def get_markup(self) -> IKMarkup:
        navigation_buttons: List[IKButton] = []

        if self.page_idx > 0:
            navigation_buttons.append(
                IKButton('قبلی', callback_data=Callback.PREVIOUS))
        if self.page_idx < self.num_pages - 1:
            navigation_buttons.append(
                IKButton('بعدی', callback_data=Callback.NEXT))

        return IKMarkup([navigation_buttons, [IKButton('بازگشت', callback_data=Callback.BACK)]])
