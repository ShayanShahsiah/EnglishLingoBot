from typing import List, Optional, Union, Dict
from telegram import InlineKeyboardMarkup as IKMarkup, InlineKeyboardButton as IKButton, Update, Bot, Message, error
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
        """
        if len(self._post_stack) <= 1:
            return None
        del self._post_stack[-1]
        return self._post_stack[-1]
    def newest(self, return_copy = False):
        """
        return (optionally copy or reference to) newest post handler
        """
        if self._post_stack:
            if return_copy:
                return deepcopy(self._post_stack[-1])
            else:
                return self._post_stack[-1]
        return None
    def get_first(self, type: str, get_first_not = False):
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
    def __repr__(self):
        return f"Int: {self._stack_index} , Data: {self._post_stack}"
        
class HistoryHandler():
    def __init__(self):
        self._navigational_post: Dict[int, NavigationalPostHandler] = dict()
        # posts that are flagged as "to be removed"
        self._removal_messages: Dict[int, List[List[int]]] = dict()
        self._latest_message_id: Dict[int, int] = dict()
        # self.load_from_db()
    def load_from_db(self):
        raise NotImplementedError
    def write_to_db(self):
        raise NotImplementedError
        #other data to save here:
    def cleanup(self):
        """
        cleanup empty lists, and possibly superfluous data
        run this periodically
        """
        for owner_id in self._navigational_post:
            if not self._navigational_post[owner_id]:
                del self._navigational_post[owner_id]
        
    def add_to_removal_stack(self, owner: Update, offset = 0):
        """
        add message at offset from current message in chat to removal stack
        if the message is already in removal stack, assert and don't add to removal stack
        """
        owner_id = owner._effective_user.id
        if owner_id in self._latest_message_id:
            if self._latest_message_id[owner_id] < owner._effective_message.message_id:
                self._latest_message_id[owner_id] = owner._effective_message.message_id
        else:
            self._latest_message_id[owner_id] = owner._effective_message.message_id
        data = [owner._effective_chat.id, self._latest_message_id[owner_id] + offset]
        if owner_id in self._removal_messages:
            assert data not in self._removal_messages[owner_id], "already in removal stack, change offset"
            self._removal_messages[owner_id].append(data)
        else:
            self._removal_messages[owner_id] = [data]
        self._latest_message_id[owner_id] += offset
    def add_to_removal_stack_lite(self, owner_id: int, chat_id: int, message_id: int, offset = 0):
        """
        lite version with need for minimum arguments
        use when Update object is not present
        """
        if owner_id in self._latest_message_id:
            if self._latest_message_id[owner_id] < message_id:
                self._latest_message_id[owner_id] = message_id
        else:
            self._latest_message_id[owner_id] = message_id
        # print(str(self._latest_message_id[owner_id]) + " is latest")
        data = [chat_id, self._latest_message_id[owner_id] + offset]
        if owner_id in self._removal_messages:
            assert data not in self._removal_messages[owner_id], "already in removal stack, change offset"
            self._removal_messages[owner_id].append(data)
        else:
            self._removal_messages[owner_id] = [data]
        self._latest_message_id[owner_id] += offset
    def clear_removal_stack(self, bot: Bot, owner: Update, removal_type: str = None):
        """
        deletes all posts in chat that are in removal stack
        optional type specifier to only remove that type: NOT IMPLEMENTED YET
        requires a bot object used to remove the messages
        """
        owner_id = owner._effective_user.id
        if owner_id in self._latest_message_id:
            if self._latest_message_id[owner_id] < owner._effective_message.message_id:
                self._latest_message_id[owner_id] = owner._effective_message.message_id
        if owner_id in self._removal_messages:
            for message_list in self._removal_messages[owner_id]:
                try:
                    bot.deleteMessage(message_list[0], message_list[1])
                except error.BadRequest:
                    print("Warning, messages were not sent? removing from removal list")
                    break
            del self._removal_messages[owner_id]
    def make_navigational_post(self, owner_id: int):
        """
        creates a navigational_post for owner_id: int: ID of user: owner._effective_user.id
        if it exists, ignores it
        """
        if owner_id not in self._navigational_post:
            self._navigational_post[owner_id] = NavigationalPostHandler()
    def add_navigational_post(self, post: 'Post', owner_id: int):
        """
        add post to navigation stack, owner_id is owner._effective_user.id
        """
        #copy since objects are passed by ref
        self._navigational_post[owner_id].append(post)
    def get_navigational_post(self, owner_id: int) -> NavigationalPostHandler:
        """
        parameters:
            owner string specifies who the post belongs to, use something consistent and unique like owner._effective_user.id
        return:
            list of NavigationalPostHandlers for owner.
            returns None if it doesn't exist
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
            res += str(removal) + ' : ' + str(self._removal_messages[removal]) + '\n'
        return res
if __name__ == "__main__":
    pass
