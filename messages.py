from utils import TestStates


help_message = 'чтобы узнать мой функционал ' \
               f'.\n' \
               '/profile, чтобы увидеть данные своего профиля (работает как в лс, так и в беседе)\n' \
                'доп инфа для админа если он напишет мне это в лс'

start_message = 'Привет! /help.\n' + help_message

help_admin = '/set_fee для изменения наград за символ'


MESSAGES = {
    'start': start_message,
    'help': help_message,
    'help_a': help_admin,

}
