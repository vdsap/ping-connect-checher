import asyncio
import asyncio.subprocess as asp
import datetime

import requests
from loguru import logger

hosts = {'11400f': '100.100.220.108',
         "11400f-win": '100.120.141.115',
         'mi9t': '100.97.35.40',
         'thuban': "100.82.21.66",
         'broadwell': '100.111.126.67',
         'sap-pc': "100.73.61.145"}


async def check_ping(ip):
    logger.info(f'Pinging {ip}')
    process = await asp.create_subprocess_shell("ping -c 2 " + ip)
    await process.wait()
    exit_code = process.returncode
    logger.info(f'Exit code {exit_code}')
    if exit_code == 0:
        pingstatus = "Active"
        logger.info(pingstatus)
    else:
        pingstatus = "Network Error"
        logger.info(pingstatus)
    return pingstatus


async def ping_compare(name, ip):
    ping1 = await check_ping(ip)
    timer = datetime.datetime.now()
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
                        f"chat_id=-1001206104553&message_thread_id=619&text={name}%20internet%20DOWN")
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
                        f'chat_id=-1001206104553&message_thread_id=619&text={name}%20internet%20UP%2C%20time%'
                        f'20elapsed%3A%20{t}')
                except Exception as err:
                    logger.error(err)
                ping1 = ping2
        else:
            await asyncio.sleep(1)


async def main():
    try:
        tasks = []
        for host_name, host_ip in hosts.items():
            tasks.append(asyncio.create_task(ping_compare(host_name, host_ip)))
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info('Stopping pinger...')
        for i in tasks:
            i.cancel()
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    logger.info('Init')
    asyncio.run(main())

# TODO: complete pinger
