import asyncio
import asyncio.subprocess as asp
import contextlib
import datetime
import json

import requests
import yaml
from loguru import logger
from yaml import safe_load as load


async def conf_init():
    with open('hosts.yaml', encoding='UTF-8') as f:
        return load(f)

async def check_ping(ip):
    logger.info(f'Pinging {ip}')
    process = await asp.create_subprocess_shell("ping -c 4 " + ip)
    await process.wait()
    exit_code = process.returncode
    if exit_code == 0:
        pingstatus = "Active"
        logger.info("🟢 " + pingstatus)
    else:
        pingstatus = "Network Error"
        logger.info("🔴 " + pingstatus)
    return pingstatus


async def ping_compare(name, ip):
    ping1 = await check_ping(ip)
    timer = datetime.datetime.now()
    while True:
        with open('hosts_status.yaml', 'r') as hosts_status:
            hosts_status_yaml = load(hosts_status)
            ping2 = await check_ping(ip)
            if ping2 != ping1:
                logger.info('Status changed')
                if ping2 == "Network Error":
                    logger.info('down')
                    timer = datetime.datetime.now()
                    try:
                        requests.get(
                            f"https://api.telegram.org/bot1105929277:AAEHFVKbNdvPHNulpW-ywks8hozFpq3kNco/sendMessage?"
                            f"chat_id=-1001206104553&parse_mode=html&message_thread_id=619&text=🔴 {name}%20internet%20⬇️")
                    except Exception as err:
                        logger.error(err)
                    ping1 = ping2
                else:
                    logger.info('up')
                    t = str((datetime.datetime.now() - timer)).split(".")[0]
                    timer = datetime.datetime.now()
                    try:
                        requests.get(
                            f'https://api.telegram.org/bot1105929277:AAEHFVKbNdvPHNulpW-ywks8hozFpq3kNco/sendMessage?'
                            f'chat_id=-1001206104553&parse_mode=html&message_thread_id=619&text=🟢 {name}%20internet%20⬆️%2C%20time%'
                            f'20offline%3A%20{t}')
                    except Exception as err:
                        logger.error(err)
                    ping1 = ping2
            else:
                hosts_status_yaml[name] = ping2
                with open('hosts_status.yaml', 'w') as hosts_status_w:
                    yaml.dump(hosts_status_yaml, hosts_status_w)
                await asyncio.sleep(1)


async def main():
    while True:
        try:
            tasks = []
            started_for_str = []
            started_for_hosts = []
            hosts = await conf_init()

            for host_name, host_ip in hosts.items():
                tasks.append(asyncio.create_task(ping_compare(host_name, host_ip)))
                logger.info(f'Pinger for {host_name}-{host_ip} started')
                started_for_str.append(f'Pinger for <b>{host_name}</b> started✅')
                started_for_hosts.append(host_name)

            with open('hosts_status.yaml', 'w') as hosts_status:
                doc_yaml = []
                for i in started_for_hosts:
                    doc_yaml.append((i, ''))
                doc_yaml = dict(doc_yaml)
                yaml.dump(doc_yaml, hosts_status)

            text = 'Hosts status\n'
            text = text + '\n'.join(started_for_str)

            pinned_message_text = json.loads(
                (requests.get('https://api.telegram.org/bot1105929277:AAEHFVKbNdvPHNulpW-ywks8hozFpq3kNco/getChat?'
                              'chat_id=-1001206104553&message_thread_id=619')).text)['result']['pinned_message']
            if pinned_message_text['text'].split('\n')[0] != 'Hosts status':
                logger.info('pined message not found')
                edit_pin_message_id = json.loads(requests.get(
                    f"https://api.telegram.org/bot1105929277:AAEHFVKbNdvPHNulpW-ywks8hozFpq3kNco/sendMessage?"
                    f"chat_id=-1001206104553&parse_mode=html&message_thread_id=619&text="
                    f"{text}").text)['result']['message_id']
                logger.debug(f"""Edit_pin_message_id={edit_pin_message_id}""")
                requests.get(
                    f'https://api.telegram.org/bot1105929277:AAEHFVKbNdvPHNulpW-ywks8hozFpq3kNco/pinChatMessage?'
                    f'chat_id=-1001206104553&message_id={edit_pin_message_id}&disable_notification=True')
                logger.debug('New message pinned')
            else:
                logger.debug('Pinned message found')
                logger.debug(f'Edit_pin_message_id={pinned_message_text}')

            while True:
                await asyncio.sleep(1)
                if await conf_init() != hosts:
                    logger.info("Hosts changed, restarting")
                    requests.get(
                        f'https://api.telegram.org/bot1105929277:AAEHFVKbNdvPHNulpW-ywks8hozFpq3kNco/sendMessage?'
                        f'chat_id=-1001206104553&parse_mode=html&message_thread_id=619&text=❗️File hosts changed❗️, restarting🔄')
                    for i in tasks:
                        i.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await asyncio.gather(i)
                    break

        except KeyboardInterrupt:
            logger.info('Stopping pinger...')
            for i in tasks:
                i.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await asyncio.gather(*tasks)


if __name__ == '__main__':
    logger.info('Init')
    asyncio.run(main())

# TODO: complete pinger
