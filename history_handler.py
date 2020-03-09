from typing import List, Optional, Union, Dict
from telegram import InlineKeyboardMarkup as IKMarkup, InlineKeyboardButton as IKButton, Update, Bot, Message
from copy import deepcopy
import ui_lib


class PostHandler():
    def __init__(self, post: 'ui_lib.Post'):
        self.post: 'ui_lib.Post' = post

    def __repr__(self):
        return f"\n\tPost Content: {self.post.get_content()}\n\tPost Markup: \n\t\t{str(self.post.get_markup())[:100] + '...'}"


class NavigationalPostHandler():
    def __init__(self):
        self._post_stack: List[PostHandler] = list()
        self._stack_index: int = 0

    def pop(self):
        if self._post_stack:
            self._post_stack.pop()

    def append(self, post):
        """
        appends if it doesn't exist already
        """
        if not post in self._post_stack:
            self._post_stack.append(PostHandler(post))

    def previous(self):
        """
        returns previous, and pops current
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

    def get(self, index):
        """
        deletes proceeding
        """
        if index >= len(self._post_stack) or index <= -(len(self._post_stack)):
            raise IndexError
        del self._post_stack[index+1:]
        return self._post_stack[index]

    def get_first(self, type: str, get_first_not=False):
        """
        get the first instance of type in stack
        get_first_not specifies if it should get first that's NOT type
        deletes proceeding stuff        
        """
        for i in reversed(range(len(self._post_stack))):
            if get_first_not:
                if self._post_stack[i].post.type == type:
                    del self._post_stack[i+1:]
                    return self._post_stack[i]
            else:
                if self._post_stack[i].post.type != type:
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
        self._navigational_post: Dict[str, NavigationalPostHandler] = dict()
        # posts that are flagged as "to be removed"
        self._removal_messages: Dict[str, List[List[int]]] = dict()
        self._latest_message_id: Dict[str, int] = dict()
        # self.load_from_db()

    def load_from_db(self):
        raise NotImplementedError

    def write_to_db(self):
        raise NotImplementedError
        # other data to save here:

    def cleanup(self):
        """
        cleanup empty lists, and possibly superfluous data
        run this periodically
        """
        cleaned = dict()
        for owner_id in self._navigational_post:
            if not self._navigational_post[owner_id]:
                del self._navigational_post[owner_id]

    def add_to_removal_stack(self, owner: Update, offset=0) -> NavigationalPostHandler:
        """
        add message at offset from current message in chat to removal stack
        if the message is already in removal stack, add the message after it to removal stack
        """
        owner_id = owner._effective_user.id
        if owner_id in self._latest_message_id:
            if self._latest_message_id[owner_id] < owner._effective_message.message_id:
                self._latest_message_id[owner_id] = owner._effective_message.message_id
        else:
            self._latest_message_id[owner_id] = owner._effective_message.message_id
        print(str(self._latest_message_id[owner_id]) + " is latest")
        data = [owner._effective_chat.id,
                self._latest_message_id[owner_id] + offset]
        if owner_id in self._removal_messages:
            assert data not in self._removal_messages[owner_id], "already in removal stack, change offset"
            self._removal_messages[owner_id].append(data)
        else:
            self._removal_messages[owner_id] = [data]
        self._latest_message_id[owner_id] += offset

    def add_to_removal_stack_lite(self, owner_id: int, chat_id: int, message_id: int, offset=0):
        """
        lite version with need for minimum arguments
        """
        if owner_id in self._latest_message_id:
            if self._latest_message_id[owner_id] < message_id:
                self._latest_message_id[owner_id] = message_id
        else:
            self._latest_message_id[owner_id] = message_id
        print(str(self._latest_message_id[owner_id]) + " is latest")
        data = [chat_id, self._latest_message_id[owner_id] + offset]
        if owner_id in self._removal_messages:
            assert data not in self._removal_messages[owner_id], "already in removal stack, change offset"
            self._removal_messages[owner_id].append(data)
        else:
            self._removal_messages[owner_id] = [data]
        self._latest_message_id[owner_id] += offset

    def clear_removal_stack(self, bot: Bot, owner: Update, removal_type: str = None):
        """
        remove all posts in removal stack
        optional type specifier to only remove that type: NOT IMPLEMENTED YET
        requires a bot object used to remove the messages
        """
        owner_id = owner._effective_user.id
        if owner_id in self._latest_message_id:
            if self._latest_message_id[owner_id] < owner._effective_message.message_id:
                self._latest_message_id[owner_id] = owner._effective_message.message_id
        if owner_id in self._removal_messages:
            for message_list in self._removal_messages[owner_id]:
                bot.deleteMessage(message_list[0], message_list[1])
            del self._removal_messages[owner_id]

    def make_navigational_post(self, owner_id: int) -> NavigationalPostHandler:
        """
        creates a navigational_post for owner_id: int: ID of user
        if it exists, ignores it
        """
        if owner_id not in self._navigational_post:
            self._navigational_post[owner_id] = NavigationalPostHandler()

    def add_navigational_post(self, post: 'ui_lib.Post', owner_id: int):
        # copy since objects are passed by ref
        copied = deepcopy(post)
        self._navigational_post[owner_id].append(copied)

    def get_navigational_post(self, owner_id: int) -> NavigationalPostHandler:
        """
        parameters:
            owner string specifies who the post belongs to, use something consistent like update.callback_query.from_user['id']
        return:
            list of navigational_post_handlers for owner.
            creates a list if it doesn't exist already
        """
        if not owner_id in self._navigational_post:
            return None
        return self._navigational_post[owner_id]

    def clear_navigational_post(self, owner_id: int):
        """
        clear previous post data, in case it's not needed
        """
        if owner_id in self._navigational_post:
            del self._navigational_post[owner_id]
        return True

    def __repr__(self):
        res = "Nav Posts\n"
        for owner_id in self._navigational_post:
            res += f"\nOwner: {owner_id} \nData: {self._navigational_post[owner_id]}"
        res += "\nRemoval Posts\n"
        for removal in self._removal_messages:
            res += str(removal) + ' : ' + \
                str(self._removal_messages[removal]) + '\n'
        return res


if __name__ == "__main__":
    pass
