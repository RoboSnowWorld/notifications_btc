import threading
import time

import telebot
from telebot import types
import requests
import json

bot = telebot.TeleBot('5875991889:AAH-Xn-jqcYK94TeV6ITUyahaZJRKx82_D0')

platform_state = ''
state = ''
chats = {'bitpapa': -1001679514902,
         'localbtc': -1001298069718,
         'transactions': -859327966}
already_checked = {}
admin_user_id = 5945088520

general_markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
generalbtn_1 = types.KeyboardButton('Добавить кошелек 💰')
generalbtn_2 = types.KeyboardButton('Добавить пользователя 👤')
generalbtn_4 = types.KeyboardButton('Список пользователей 📃')
general_markup.add(generalbtn_1, generalbtn_2, generalbtn_4)

def check_wallets():
    while True:
        with open('last_transactions.json') as f:
            last_transactions_json = f.read()
        last_transactions = json.loads(last_transactions_json)
        for wallet in last_transactions.keys():
            time.sleep(5)
            check_transfers(wallet, last_transactions[wallet][1])

def check_users():
    while True:
        with open('users.json') as f:
            users_json = f.read()
        users = json.loads(users_json)

        for user in users['bitpapa'].split('\n'):
            check_user_online(user, 'bitpapa')
        for user in users['localbtc'].split('\n'):
            check_user_online(user, 'localbtc')


def check_user_online(username, platform):
    global already_checked
    if platform == 'bitpapa':
        headers = {'Content-Type': 'application/json'}
        try:
            r = requests.get(f'https://bitpapa.com/api/v1/profiles/{username}', headers=headers)
            r.json()
        except:
            return
        online = r.json()['profile']['online']
    elif platform == 'localbtc':
        try:
            r = requests.get(f'https://localbitcoins.com/accounts/profile/{username}')
        except:
            return
        online = 'just now' in r.text

    if online:
        bot.send_message(chats[platform], f'Пользователь {username} был только что в сети')


def check_transfers(wallet, name):
    headers = {'Content-Type': 'application/json'}
    try:
        r = requests.get(f'https://blockchain.info/rawaddr/{wallet}', headers=headers)
    except:
        return
#    r = requests.get('https://bitpapa.com/api/v1/transactions?query=bc1qa9atyfdp57cfjt0xrm7mdh2ywwfvmy7z9ge3s9', headers=headers)
    if r.status_code == 404:
        with open('last_transactions.json') as f:
            last_transactions_json = f.read()
        last_transactions = json.loads(last_transactions_json)
        del last_transactions[wallet]
        last_transactions_json = json.dumps(last_transactions)
        with open("last_transactions.json", "w") as my_file:
            my_file.write(last_transactions_json)
        return
    elif r.status_code == 429:
        return

    transactions = r.json()['txs']
    if not transactions:
        return
    last_transaction = transactions[0]['hash']
    with open('last_transactions.json') as f:
        last_transactions_json = f.read()
    last_transactions = json.loads(last_transactions_json)
    if last_transactions[wallet][0] != last_transaction:
        summ = transactions[0]["out"][0]["value"]
        if len(str(summ)) < 9:
            summ_output = '0.' + '0' * (8 - len(str(summ))) + str(summ)
        else:
            summ_output = str(summ)[:2] + '.' + str(summ)[2:]
        bot.send_message(chats['transactions'], f'Новая транзакция на кошелек {name} {wallet} сумма {summ_output}')
        last_transactions[wallet][0] = last_transaction
    last_transactions_json = json.dumps(last_transactions)
    with open("last_transactions.json", "w") as my_file:
        my_file.write(last_transactions_json)


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, 'Настройка уведомлений 🔔', reply_markup=general_markup)

@bot.message_handler(content_types=['text'])
def incoming_message(message):
    global state
    global platform_state
   # if message.from_user.id != admin_user_id:
    #    return
    if message.text == 'Добавить кошелек 💰':
        state = 'add_wallet'
        bot.send_message(message.chat.id, 'Введите номер кошелька')
    elif 'Добавить пользователя' in message.text:
        bot.send_message(message.chat.id, 'Введите ник пользователя')
        state = 'add_user'
    elif 'Список пользователей 📃' in message.text:
        users_out = ''
        if message.chat.id == chats['bitpapa']:
            with open('users.json') as f:
                users_json = f.read()
            users_out = json.loads(users_json)['bitpapa']
        elif message.chat.id == chats['localbtc']:
            with open('users.json') as f:
                users_json = f.read()
            users_out = json.loads(users_json)['localbtc']
        bot.send_message(message.chat.id, users_out)
    elif state == 'add_wallet':
        with open('last_transactions.json') as f:
            last_transactions_json = f.read()
        last_transactions = json.loads(last_transactions_json)
        last_transactions[message.text] = ['None', 'undefined']
        last_transactions_json = json.dumps(last_transactions)
        with open("last_transactions.json", "w") as my_file:
            my_file.write(last_transactions_json)
        bot.send_message(message.chat.id, 'Введите имя кошелька')
        state = 'create_wallet_name'
    elif state == 'create_wallet_name':
        with open('last_transactions.json') as f:
            last_transactions_json = f.read()
        last_transactions = json.loads(last_transactions_json)
        undefined_wallet = ''
        for wallet in last_transactions.keys():
            if last_transactions[wallet][1] == 'undefined':
                undefined_wallet = wallet
        last_transactions[undefined_wallet] = ['None', message.text]
        last_transactions_json = json.dumps(last_transactions)
        with open("last_transactions.json", "w") as my_file:
            my_file.write(last_transactions_json)
        bot.send_message(message.chat.id, 'Успешно ✅')
        start_command(message)
    elif state == 'add_user':
        if message.chat.id == chats['bitpapa']:
            if message.text[0] == '-':
                with open('users.json') as f:
                    users_json = f.read()
                    users = json.loads(users_json)
                    index = users['bitpapa'].find(message.text[1:])
                    users['bitpapa'] = users['bitpapa'][:index] + users['bitpapa'][index + len(message.text) + 1:]
                with open('users.json','w') as f:
                    users_json = json.dumps(users)
                    f.write(users_json)
            else:
                with open('users.json') as f:
                    users_json = f.read()
                    users = json.loads(users_json)
                    users['bitpapa'] += message.text + '\n'
                with open('users.json', 'w') as f:
                    users_json = json.dumps(users)
                    f.write(users_json)
        elif message.chat.id == chats['localbtc']:
            if message.text[0] == '-':
                with open('users.json') as f:
                    users_json = f.read()
                    users = json.loads(users_json)
                    index = users['localbtc'].find(message.text[1:])
                    users['localbtc'] = users['localbtc'][:index] + users['localbtc'][index + len(message.text) + 1:]
                with open('users.json','w') as f:
                    users_json = json.dumps(users)
                    f.write(users_json)
            else:
                with open('users.json') as f:
                    users_json = f.read()
                    users = json.loads(users_json)
                    users['bitpapa'] += message.text + '\n'
                with open('users.json', 'w') as f:
                    users_json = json.dumps(users)
                    f.write(users_json)
        bot.send_message(message.chat.id, 'Успешно ✅')
        start_command(message)

checking_users_thread = threading.Thread(target=check_users)
checking_users_thread.start()

checking_transactions_thread = threading.Thread(target=check_wallets)
checking_transactions_thread.start()

while True:
    try:
        bot.polling()
    except:
        pass