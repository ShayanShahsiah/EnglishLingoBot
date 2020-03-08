from typing import List, Optional, Union, Dict
from telegram import InlineKeyboardMarkup as IKMarkup, InlineKeyboardButton as IKButton, Update, Bot, Message
from copy import deepcopy


class post_handler():
    def __init__(self, post: 'Post'):
        self.post: 'Post' = post
    def __repr__(self):
        return f"\n\tPost Content: {self.post.get_content()}\n\tPost Markup: \n\t\t{str(self.post.get_markup())[:100] + '...'}"
class navigational_post_handler():
    def __init__(self):
        self._post_stack: List[post_handler] = list()
        self._stack_index: int = 0
    def pop(self):
        if self._post_stack:
            self._post_stack.pop()
    def append(self, post: 'Post'):
        """
        appends if it doesn't exist already
        """
        if not post in self._post_stack:
            self._post_stack.append(post_handler(post))
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
        self._removal_messages: Dict[str, List[List[int, int]]] = dict()
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
        cleaned = dict()
        for owner_id in self._navigational_post:
            if not self._navigational_post[owner_id]:
                del self._navigational_post[owner_id]
    def add_to_removal_stack_short(self, message: Message, owner: Update) -> navigational_post_handler:
        """
        add a post to removal stack. The posts will remain here until clear_removal_stack is called
        * shorter version
        """
        #copy since objects are passed by ref
        owner_id = owner._effective_user.id
        data = [message.chat_id, message.message_id]
        if owner_id in self._removal_messages:
            if data in self._removal_messages[owner_id]: 
                #already in removal stack, use next message_id
                return False
            self._removal_messages[owner_id].append(data)
        else:
            self._removal_messages[owner_id] = [data]
        return True
    def add_to_removal_stack(self, chat_id: int, message_id: int, owner_id: int) -> navigational_post_handler:
        """
        add a post to removal stack. The posts will remain here until clear_removal_stack is called
        * light version
        """
        data = [chat_id, message_id]
        if owner_id in self._removal_messages:
            if data in self._removal_messages[owner_id]: 
                #already in removal stack, use next message_id
                return False
            self._removal_messages[owner_id].append(data)
        else:
            self._removal_messages[owner_id] = [data]
        return True
    def clear_removal_stack(self, bot: Bot, owner: Update, removal_type: str = None):
        """
        remove all posts in removal stack
        optional type specifier to only remove that type: NOT IMPLEMENTED YET
        requires a bot object used to remove the messages
        """
        owner_id = owner._effective_user.id
        if owner_id in self._removal_messages:
            for message_list in self._removal_messages[owner_id]:
                bot.deleteMessage(message_list[0], message_list[1])
            del self._removal_messages[owner_id]
    def make_navigational_post(self, owner_id: int)-> navigational_post_handler:
        """
        creates a navigational_post for owner_id: int: ID of user
        if it exists, ignores it
        """
        if owner_id not in self._navigational_post:
            self._navigational_post[owner_id] = navigational_post_handler()
    def add_navigational_post(self, post: 'Post', owner_id: int):
        #copy since objects are passed by ref
        copied = deepcopy(post)
        self._navigational_post[owner_id].append(copied)
    def get_navigational_post(self, owner_id: int) -> navigational_post_handler:
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
            res += str(removal) + '\n'
        return res
if __name__ == "__main__":
    pass
