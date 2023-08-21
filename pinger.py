import asyncio
import asyncio.subprocess as asp
import contextlib
import datetime
import json
from asyncio import Task

import requests
import yaml
from loguru import logger
from yaml import safe_load as load

bot_text_url = ''


async def conf_init():
    with open('hosts.yaml', encoding='UTF-8') as f:
        return load(f)


async def host_init(hosts, tasks, started_for_str, started_for_hosts):
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


async def host_status_change(name, pingstatus):
    with open('hosts_status.yaml', 'r') as hosts_status:
        hosts_status_yaml = load(hosts_status)
    hosts_status_yaml[name] = pingstatus
    with open('hosts_status.yaml', 'w') as hosts_status:
        yaml.dump(hosts_status_yaml, hosts_status)


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


async def check_ping_tailscale(ip):
    logger.info(f'Pinging {ip}')
    process = await asp.create_subprocess_shell("tailscale ping " + ip)
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
    global bot_text_url
    ping1 = await check_ping_tailscale(ip)
    timer = datetime.datetime.now()
    await host_status_change(name, ping1)
    while True:
        ping2 = await check_ping_tailscale(ip)
        if ping2 != ping1:
            logger.info('Status changed')
            if ping2 == "Network Error":
                logger.info('down')
                await host_status_change(name, ping2)
                timer = datetime.datetime.now()
                try:
                    requests.get(
                        f"{bot_text_url}/sendMessage?"
                        f"chat_id=-1001206104553&parse_mode=html&message_thread_id=619&text=🔴 {name}%20internet%20⬇️")
                except Exception as err:
                    logger.error(err)
                ping1 = ping2
            else:
                logger.info('up')
                await host_status_change(name, ping2)
                t = str((datetime.datetime.now() - timer)).split(".")[0]
                timer = datetime.datetime.now()
                try:
                    requests.get(
                        f'{bot_text_url}/sendMessage?'
                        f'chat_id=-1001206104553&parse_mode=html&message_thread_id=619&'
                        f'text=🟢 {name}%20internet%20⬆️%2C%20time%20offline%3A%20{t}')
                except Exception as err:
                    logger.error(err)
                ping1 = ping2
        else:
            await asyncio.sleep(1)


async def changing_host(tasks):
    global bot_text_url
    logger.info("Hosts changed, restarting")
    try:
        requests.get(
            f'{bot_text_url}/sendMessage?'
            f'chat_id=-1001206104553&parse_mode=html&message_thread_id=619&'
            f'text=❗️File hosts changed❗️, restarting🔄')
    except Exception as err:
        logger.error(err)
    for i in tasks:
        i.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(i)


async def host_status_read():
    with open('hosts_status.yaml', 'r') as hosts_status:
        return load(hosts_status)


async def tg_message(started_for_str):
    global bot_text_url
    text = 'Hosts status\n'
    text_out = text + '\n'.join(started_for_str)
    try:
        edit_pin_message_id = json.loads(
            (requests.get(bot_text_url + '/getChat?chat_id=-1001206104553')).text)['result']['pinned_message']
        if edit_pin_message_id['text'].split('\n')[0] != 'Hosts status':
            logger.info('pined message not found')
            edit_pin_message_id = json.loads(requests.get(
                f"{bot_text_url}/sendMessage?"
                f"chat_id=-1001206104553&parse_mode=html&message_thread_id=619&text={text_out}").text)['result'][
                'message_id']
            logger.debug(f"""Edit_pin_message_id={edit_pin_message_id}""")
            logger.info(requests.get(
                f'{bot_text_url}/pinChatMessage?'
                f'chat_id=-1001206104553&message_id={edit_pin_message_id}&disable_notification=True'))
            logger.debug('New message pinned')
        else:
            logger.debug('Pinned message found')
            logger.debug(f'Edit_pin_message_id={edit_pin_message_id}')
    except Exception as err:
        logger.error(err)
    while True:
        text_out = text
        await asyncio.sleep(5)
        host_yaml = await host_status_read()
        for name, status in host_yaml.items():
            if status == "Network Error":
                text_out += f'🔴 {name}\n'
            else:
                text_out += f'🟢 {name}\n'
        try:
            logger.info(requests.get(bot_text_url + f'/editMessageText?chat_id=-1001206104553&'
                                                f'message_id={edit_pin_message_id}&text={text_out}'))
        except Exception as err:
            logger.error(err)


async def main():
    global bot_text_url
    bot_text_url = "https://api.telegram.org/bot1105929277:AAEHFVKbNdvPHNulpW-ywks8hozFpq3kNco"
    while True:
        tasks: list[Task[None]] = []
        try:
            started_for_str = []
            started_for_hosts = []
            hosts = await conf_init()

            await host_init(hosts, tasks, started_for_str, started_for_hosts)

            await tg_message(started_for_str)

            while True:
                await asyncio.sleep(1)
                if await conf_init() != hosts:
                    await changing_host(hosts)
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
