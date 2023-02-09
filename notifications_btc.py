import threading
import time

import telebot
from telebot import types
import requests
import json
from lbcapi import api

bot = telebot.TeleBot('5875991889:AAH-Xn-jqcYK94TeV6ITUyahaZJRKx82_D0')

platform_state = ''
state = ''
chats = {'bitpapa': -1001679514902,
         'localbtc': -1001298069718,
         'transactions': -1001800331790}
already_checked = {}
admin_user_id = 5945088520

general_markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
generalbtn_1 = types.KeyboardButton('Добавить кошелек 💰')
generalbtn_2 = types.KeyboardButton('Добавить пользователя 👤')
generalbtn_3 = types.KeyboardButton('Добавить обьявление ✅')
generalbtn_4 = types.KeyboardButton('Список пользователей 📃')
general_markup.add(generalbtn_1, generalbtn_2, generalbtn_3, generalbtn_4)

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
            time.sleep(2)
            check_user_online(user, 'bitpapa')
        for user in users['localbtc'].split('\n'):
            time.sleep(2)
            check_user_online(user, 'localbtc')

def check_ads():
    while True:
        with open('ads.json') as f:
            ads_json = f.read()
        ads = json.loads(ads_json)
        for ad in ads['bitpapa']:
            for user in ad.keys():
                time.sleep(2)
                check_ad('bitpapa', user, ad[user])
        for ad in ads['localbtc']:
            for user in ad.keys():
                time.sleep(2)
                check_ad('localbtc', user, ad[user])

def check_ad(platform, user, uid):
    if uid == 'None':
        return
    current_price = ' '
    changed = False
    with open('last_prices.json') as f:
        last_prices_json = f.read()
    last_prices = json.loads(last_prices_json)
    if platform == 'bitpapa':
        try:
            r = requests.get(f'https://bitpapa.com/api/v1/offers/of/{user}')
            offers = r.json()['ads']
            currency = 'RUB'
        except:
            return
        for offer in offers:
            if offer['id'].split('-')[0] == uid:
                current_price = str(offer['limit_min']).split('.')[0] + ' - ' + str(offer['limit_max']).split('.')[0]


    elif platform == 'localbtc':
       conn = api.hmac('eaced972f2349d480a43aa7540c5ad9a', 'cd811b5051ba8296a8e1f9a9503256bd2d012e5230efaa6a40eb7624165c2283')
       res = conn.call('GET', f'/api/ad-get/{uid}/').json()
       currency = res['data']['ad_list'][0]['data']['currency']
       min_amount = res['data']['ad_list'][0]['data']['min_amount_available']
       max_amount = res['data']['ad_list'][0]['data']['max_amount_available']
       if max_amount == '31000.00' or max_amount == '0.00':
           current_price = ' '
       else:
           current_price = f'{min_amount} - {max_amount}'
    last_price = last_prices[uid]
    if current_price != last_price:
        changed = True
    last_prices[uid] = current_price
    if changed:
        bot.send_message(chats[platform], f'В обьявлении {uid} пользователя {user} Изменились ограничения.\n'
                                      f'Было: {last_price} {currency}\nСтало: {current_price} {currency}')
    last_prices_json = json.dumps(last_prices)
    with open('last_prices.json','w') as f:
        f.write(last_prices_json)


def check_user_online(username, platform):
    global already_checked
    online = False
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
        if 'just now' in r.text or '1 minute ago' in r.text or '2 minutes ago' in r.text:
            online = True

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
    wallets_with_amounts_input = ''
    if len(transactions[0]['inputs']) > 5:
        transactions[0]['inputs'] = transactions[0]['inputs'][:5]
    for inp in transactions[0]['inputs']:
        summ = inp['prev_out']['value']
        if len(str(summ)) < 9:
            summ_output = '0.' + '0' * (8 - len(str(summ))) + str(summ)
        else:
            summ_output = str(summ)[0] + '.' + str(summ)[1:]
        if inp['prev_out']['addr'] == wallet:
            wallets_with_amounts_input += f'**{summ_output}**' + '\n' + inp['prev_out']['addr'] + '\n'
        else:
            wallets_with_amounts_input += summ_output + '\n' + inp['prev_out']['addr'] + '\n'

    wallets_with_amounts_output = ''
    for inp in transactions[0]['out']:
        summ = inp['value']
        if len(str(summ)) < 9:
            summ_output = '0.' + '0' * (8 - len(str(summ))) + str(summ)
        else:
            summ_output = str(summ)[0] + '.' + str(summ)[1:]
        if inp['addr'] == wallet:
            wallets_with_amounts_output += f'**{summ_output}**' + '\n' + inp['addr'] + '\n'
        else:
            wallets_with_amounts_output += summ_output + '\n' + inp['addr'] + '\n'

    with open('last_transactions.json') as f:
        last_transactions_json = f.read()
    last_transactions = json.loads(last_transactions_json)
    if last_transactions[wallet][0] != last_transaction:
        summ = transactions[0]["out"][0]["value"]
        if len(str(summ)) < 9:
            summ_output = '0.' + '0' * (8 - len(str(summ))) + str(summ)
        else:
            summ_output = str(summ)[0] + '.' + str(summ)[1:]
        bot.send_message(chats['transactions'], f'Новая транзакция на кошелек\n**{name}**\n{last_transaction}\n\nна\n{wallets_with_amounts_output}\n\nС\n{wallets_with_amounts_input}')
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
    elif 'Добавить обьявление' in message.text:
        bot.send_message(message.chat.id, 'Введите ник')
        state = 'set_nickname_ad'
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
    elif state == 'set_nickname_ad':
        with open('ads.json') as f:
            ads_json = f.read()
        ads = json.loads(ads_json)
        if message.chat.id == chats['bitpapa']:
            ads['bitpapa'].append({message.text: 'None'})

        elif message.chat.id == chats['localbtc']:
            ads['localbtc'].append({message.text: 'None'})
        ads_json = json.dumps(ads)
        with open('ads.json','w') as f:
            f.write(ads_json)
        bot.send_message(message.chat.id, 'Установите id обьявления')
        state = 'set_uid_ad'
    elif state == 'set_uid_ad':
        with open('last_prices.json') as f:
            last_prices_json = f.read()
        last_prices = json.loads(last_prices_json)
        last_prices[message.text] = ' '
        with open('last_prices.json','w') as f:
            last_prices_json = json.dumps(last_prices)
            f.write(last_prices_json)
        with open('ads.json') as f:
            ads_json = f.read()
        ads = json.loads(ads_json)
        if message.chat.id == chats['bitpapa']:
            for ad in ads['bitpapa']:
                for username in ad.keys():
                    if ad[username] == 'None':
                        ad[username] = message.text
        elif message.chat.id == chats['localbtc']:
            for ad in ads['localbtc']:
                for username in ad.keys():
                    if ad[username] == 'None':
                        ad[username] = message.text
        with open('ads.json','w') as f:
            ads_json = json.dumps(ads)
            f.write(ads_json)
        bot.send_message(message.chat.id, 'Успешно ✅')
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
                    users['bitpapa'] = users['bitpapa'][:index] + users['bitpapa'][index + len(message.text):]
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
                    users['localbtc'] = users['localbtc'][:index] + users['localbtc'][index + len(message.text):]
                with open('users.json','w') as f:
                    users_json = json.dumps(users)
                    f.write(users_json)
            else:
                with open('users.json') as f:
                    users_json = f.read()
                    users = json.loads(users_json)
                    users['localbtc'] += message.text + '\n'
                with open('users.json', 'w') as f:
                    users_json = json.dumps(users)
                    f.write(users_json)
        bot.send_message(message.chat.id, 'Успешно ✅')
        start_command(message)

checking_users_thread = threading.Thread(target=check_users)
checking_users_thread.start()

checking_transactions_thread = threading.Thread(target=check_wallets)
checking_transactions_thread.start()

checking_transactions_thread = threading.Thread(target=check_ads)
checking_transactions_thread.start()

while True:
    try:
        bot.polling()
    except:
        pass