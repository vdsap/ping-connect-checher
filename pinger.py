import asyncio
import asyncio.subprocess as asp
import datetime

import requests
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
    requests.get(
        f"https://api.telegram.org/bot1105929277:AAEHFVKbNdvPHNulpW-ywks8hozFpq3kNco/sendMessage?"
        f"chat_id=-1001206104553&parse_mode=html&message_thread_id=619&text=Pinger for <b>{name}</b> started")
    while True:
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
            await asyncio.sleep(1)


async def main():
    while True:
        try:
            tasks = []
            hosts = await conf_init()
            for host_name, host_ip in hosts.items():
                tasks.append(asyncio.create_task(ping_compare(host_name, host_ip)))
            while True:
                await asyncio.sleep(1)
                if await conf_init() != hosts:
                    logger.info("Hosts changed, restarting")
                    requests.get(
                        f'https://api.telegram.org/bot1105929277:AAEHFVKbNdvPHNulpW-ywks8hozFpq3kNco/sendMessage?'
                        f'chat_id=-1001206104553&parse_mode=html&message_thread_id=619&text=File hosts changed, restarting')
                    for i in tasks:
                        i.cancel()
                    await asyncio.gather(*tasks)
                    break
        except KeyboardInterrupt:
            logger.info('Stopping pinger...')
            for i in tasks:
                i.cancel()
            await asyncio.gather(*tasks)


if __name__ == '__main__':
    logger.info('Init')
    asyncio.run(main())

# TODO: complete pinger
