from discord.ext import tasks, commands
import logging
import discord
import requests
import json
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)



############################################################################################
TOKEN = '____________________________TOKEN___________________________'
channel_ID = 9999999999999999999
API_call_loop_period = 30
safes = {
    '0xB65cef03b9B89f99517643226d76e286ee999e77': ['dev', 'Mainnet', 3],
    '0x468A0FF843BC5D185D7B07e4619119259b03619f': ['dev', 'Arbitrum', 3],
    '0x329543f0F4BB134A3f7a826DC32532398B38a3fA': ['dev', 'Binance Smart Chain', 2],
    '0x4977110Ed3CD5eC5598e88c8965951a47dd4e738': ['dev', 'Polygon', 3],
    '0x86cbD0ce0c087b482782c181dA8d191De18C8275': ['techops', 'Mainnet', 3],
    '0x292549E6bd5a41aE4521Bb8679aDA59631B9eD4C': ['techops', 'Arbitrum', 3],
    '0x777061674751834993bfBa2269A1F4de5B4a6E7c': ['techops', 'Binance Smart Chain', 3],
    '0xeb7341c89ba46CC7945f75Bd5dD7a04f8FA16327': ['techops', 'Polygon', 3],
    '0xD0A7A8B98957b9CD3cFB9c0425AbE44551158e9e': ['treasury_vault', 'Mainnet', 3],
    '0x042B32Ac6b453485e357938bdC38e0340d4b9276': ['treasury_ops', 'Mainnet', 3],
    '0x337a32FA07eD51Aae1a7923427063B299A2307bd': ['treasury_ops', 'Fantom', 3],
    '0xD4868d98849a58F743787c77738D808376210292': ['fin_ops', 'Mainnet', 3],
    '0x6F76C6A1059093E21D8B1C13C4e20D8335e2909F': ['politician', 'Mainnet', 3],
    '0xB76782B51BFf9C27bA69C77027e20Abd92Bcf3a8': ['ibbtc', 'Mainnet', 3],
    '0x9faA327AAF1b564B569Cb0Bc0FDAA87052e8d92c': ['recovered', 'Mainnet', 3]
}
#############################################################################################


##### if using dotenv #####
# from dotenv import load_dotenv
# import dotenv
# load_dotenv()
# TOKEN = os.getenv('DISCORD_TOKEN_' + TICKER)


bot = commands.Bot(command_prefix=['.'])
prev_safeTxHash = []
try:
    with open('prev_safeTxHash.json', 'r') as lst:
        prev_safeTxHash = json.load(lst)
    print('json loaded')
    print(prev_safeTxHash)
except:
    print('File not found, will rebuild hash list.')

# delagates = []
# owners = [
#     "0x4C16BF1f3acbCbF2b05291e8120DaCC05c10586E",
#     "0x54cF9dF9dCd78E470AB7CB892D7bFbE114c025fc",
#     "0xaF94D299a73c4545ff702E79D16d9fb1AB5BDAbF",
#     "0x59c68A651a1f49C26145666E9D5647B1472912A9",
#     "0x15b8Fe651C268cfb5b519cC7E98bd45C162313C2"
# ]

headers = {
    'accept': 'application/json'
}
loop_count = 0


def fetch_thresholds(address):
    try:
        # url = f'https://safe-transaction.gnosis.io/api/v1/safes/{address}/all-transactions/?ordering=submissionDate&limit=150&executed=false&queued=true&trusted=false'
        print(address)
        url = f'https://safe-transaction.gnosis.io/api/v1/safes/{address}/'
        response = requests.get(url, headers=headers)
        print(response.text)
        r = json.loads(response.text)
        threshold = r['threshold']
        print('threshold:', threshold)
        return threshold
    except Exception as e:
        print("error, safe not found on API, address:", address + ", reverting to default value")
        print(str(e))
        return -1


print('fetching thresholds...')
try:
    for safe in safes:
        threshold = fetch_thresholds(safe)
        if threshold != -1:
            safes[safe][2] = threshold
        time.sleep(.2)
    print('done')
except Exception as e:
    print('error fetching thresholds')
    print(str(e))

print(safes)


def gnosis_api_call(address):
    try:
        # url = f'https://safe-transaction.gnosis.io/api/v1/safes/{address}/all-transactions/?ordering=submissionDate&limit=150&executed=false&queued=true&trusted=false'
        url = f'https://safe-transaction.gnosis.io/api/v1/safes/{address}/multisig-transactions/?limit=5'
        response = requests.get(url, headers=headers)
        r = json.loads(response.text)
        return r
    except Exception as e:
        print("API call error " + str(e))


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='Safes', status=discord.Status.online))


@tasks.loop(seconds=API_call_loop_period)
async def get_data():
    try:
        global loop_count
        channel = bot.get_channel(channel_ID)
        for address in safes:
            # print(address, safes[address])
            for safe_tx in gnosis_api_call(address)['results']:
                try:
                    to = safe_tx['to']
                    creationDate = safe_tx['submissionDate'].split('.')[0].replace('T', ' ').replace('Z', ' ')
                    modifiedDate = safe_tx['modified'].split('.')[0].replace('T', ' ').replace('Z', ' ')
                    safeTxHash = safe_tx['safeTxHash']
                    is_executed = safe_tx['isExecuted']
                    if [safeTxHash, modifiedDate, is_executed] not in prev_safeTxHash:
                        print('Safe:', address, safes[address][0], safes[address][1])
                        print('to:', safe_tx['to'])
                        print('creationDate:', creationDate)
                        print('modifiedDate:', modifiedDate)
                        prev_safeTxHash.append([safeTxHash, modifiedDate, is_executed])
                        print('safeTxHash:', safeTxHash)
                        if safe_tx['dataDecoded'] is None:
                            method = 'None'
                        else:
                            method = safe_tx['dataDecoded']['method']
                        print('method:', method)
                        if safe_tx['isSuccessful'] is None:
                            isSuccessful = 'n/a'
                        else:
                            if safe_tx['isSuccessful'] == True:
                                isSuccessful = 'Success'
                            else:
                                isSuccessful = 'Fail'

                        print('staus:', isSuccessful)

                        if safe_tx['transactionHash'] is None:
                            TxHash = 'n/a'
                            etherscan_link = 'n/a'
                        else:
                            TxHash = safe_tx['transactionHash']
                            if safes[address][1] == 'Mainnet':
                                etherscan_link = f'https://etherscan.io/tx/{TxHash}'
                            elif safes[address][1] == 'Binance Smart Chain':
                                etherscan_link = f'https://bscscan.com/tx/{TxHash}'
                            elif safes[address][1] == 'Polygon':
                                etherscan_link = f'https://polygonscan.com/tx/{TxHash}'
                            elif safes[address][1] == 'Arbitrum':
                                etherscan_link = f'https://arbiscan.io/tx/{TxHash}'
                            elif safes[address][1] == 'Fantom':
                                etherscan_link = f'https://ftmscan.com/tx/{TxHash}'
                            else:
                                etherscan_link = f'https://etherscan.io/tx/{TxHash}'

                        print('TxHash:', TxHash)
                        print('etherscan_link:', etherscan_link)
                        gnosis_link = f'https://gnosis-safe.io/app/eth:{address}/transactions/{safeTxHash}'
                        print('gnosis_link:', gnosis_link)
                        confirmations = safe_tx['confirmations']
                        print('safeTxHash:', safeTxHash)
                        all_sigs_collected = False
                        confirmationsRequired = safes[address][2]
                        print('is executed:', is_executed)
                        print('confirmations:', len(confirmations))
                        print('confirmations required:', confirmationsRequired)
                        if is_executed == True:
                            line1 = '[TX EXECUTED]'
                        elif len(confirmations) == confirmationsRequired:
                            line1 = '[READY FOR EXEC]'
                        elif len(confirmations) == 0:
                            line1 = '[NEW TX]'
                        else:
                            line1 = '[EVENT]'
                        print(line1)
                        line2 = f'Safe:᲼**{safes[address][0]} ({safes[address][1]})** {address}'
                        line9 = f'Modified:᲼**{modifiedDate}**'
                        line3 = f'Created:᲼**{creationDate}**'
                        line4 = f"To:᲼**{to}**+ '\n'"
                        line5 = f"Method:᲼**{method}**+ '\n'"
                        line6 = f'safeTxHash:\n[{safeTxHash}]({gnosis_link})'
                        line7 = f'TxHash:\n[{TxHash}]({etherscan_link})'
                        line10 = f'Executed: **{is_executed}**᲼᲼Status:᲼**{isSuccessful}**'
                        line8 = f"\nSignatures collected:᲼**{len(confirmations)}**"
                        embed = discord.Embed(title=line1, description=line2 + '\n' + '\n' + line9 + '\n' + line3 + '\n' + line6 + '\n' + line7 + line8 + '\n' + line10,
                                              color=0x00ff00)
                        print(' ')
                        if loop_count!=0 and line1!= '[EVENT]':
                            await channel.send(embed=embed)
                        else:
                            pass
                except Exception as e:
                    print("parse error: " + str(e))

        print(f"{datetime.now()}loop {loop_count} complete")
        # print(prev_safeTxHash)
        loop_count += 1
        with open("prev_safeTxHash.json", "w") as outfile:
            json.dump(prev_safeTxHash, outfile)
            print(f'log saved to prev_safeTxHash.json')
    except Exception as e:
        print("main func error: " + str(e))


@get_data.before_loop
async def before_name_change():
    print('starting...')
    await bot.wait_until_ready()


get_data.start()
print('bot.run')
bot.run(TOKEN)
