import requests, re
import json
import time
from threading import Thread, Lock
from queue import Queue
from datetime import datetime

headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.5702.400 QQBrowser/10.2.1893.400"
        }
url_prefix = 'https://www.12306.cn/kfzmpt/lcxxcx/query?'
seat_ref = {
    'yz':'硬座',
    'wz':'无座',
    'swz':'商务特等座',
    'zy':'一等座',
    'ze':'二等座',
    'gr':'高级软卧',
    'rw':'软卧',
    'srrb':'动卧',
    'rz':'软座',
    'gg':'其他',
    'yw': '硬卧',

}

# the relative index of ticket numbers in train info
# start from 36
seat_file_index = {
    'A9': 12,
    'P': 12,
    'M': 11,
    'O': 10,
    'A6': 1,
    'A4': 3,
    'F': 13,
    'A3': 8,
    'A2': 4,
    'A1': 9,
    'WZ': 6,
    'F#1': 13,
    'F#3': 13,
    '3#1': 8,
    '3#2': 8,
    '3#3': 8,
    '4#3': 3,
    '4#1': 3,
    '6#1': 1,
    '6#3': 1
}

seat_price_ref = {
    'A9': '商务特等座',
    'P': '商务特等座',
    'M': '一等座',
    'O': '二等座',
    'A6': '高级软卧',
    'A4': '软卧',
    'F': '动卧',
    'A3': '硬卧',
    'A2': '软座',
    'A1': '硬座',
    'WZ': '无座',
    'F#1': '动卧下',
    'F#3': '动卧上',
    '3#1': '硬卧下',
    '3#2': '硬卧中',
    '3#3': '硬卧上',
    '4#3': '软卧上',
    '4#1': '软卧下',
    '6#1': '高级软卧下',
    '6#3': '高级软卧上'
}

def getStationList():
    url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.8971'
    response = requests.get(url, verify=False)
    stations = re.findall(r'([\u4e00-\u9fa5]+)\|([A-Z]+)', response.text)
    station_code = dict(stations)
    # station_name = dict(zip(station_code.values(), station_code.keys()))
    return station_code

def getTrainInfo(date, de_station, ar_station, station_code):
    de_station_c = station_code[de_station]
    ar_station_c = station_code[ar_station]
    # url = 'https://www.12306.cn/kfzmpt/lcxxcx/query?'
    url = url_prefix+"purpose_codes=ADULT"\
          +"&queryDate="+date\
          +"&from_station="+de_station_c \
          +"&to_station="+ar_station_c\

    print(url)
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text

# from_station_no: column 28
# to_station_no: column 29
# seat_types 26
def getTicketPrice(train_num, de_station_no, ar_station_no, seat_types, date):
    url = 'https://www.12306.cn/kfzmpt/leftTicket/queryTicketPrice?'
    dt = datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
    url = url + 'train_no=' + train_num \
            + '&from_station_no=' + de_station_no \
            + '&to_station_no=' + ar_station_no \
            + '&seat_types=' + seat_types \
            + '&train_date=' + dt
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text


def producer(generator, out_q):
    sc_keys = list(station_code.keys())
    while True:
        lock.acquire()
        try:
            args = next(generator)
        except StopIteration:
            lock.release()
            break
        lock.release()
        out_q.put(getTrainInfo(date, sc_keys[args[0]], sc_keys[args[1]], station_code))

def consumer(out_q, dataset):
    attributes = []
    cnt = 0
    while True:
        print('Tasks Finished %d / %d'%(cnt, total_num))
        response = json.loads(out_q.get())
        if response is not None:
            cnt = cnt + 1
        if ('data' in response.keys()):
            if (type(response['data']) is dict and 'datas' in response['data'].keys()):
                # print('Data obtained successfully\n')
                if (attributes is None):
                    attributes = list(response['data']['datas'][0].keys())
                    for elem in attributes:
                        dataset.write(elem + ',')
                    dataset.write('\n')
        writeTrainInfo(dataset, response)

def writeTrainInfo(file, response):
    if ('data' in response.keys()):
        if (type(response['data']) is dict and 'datas' in response['data'].keys()):
            print('Data obtained successfully\n')
            for row in response['data']['datas']:
                for elem in row.values():
                    file.write(str(elem) + ',')
                file.write('\n')
    else:
        print('Invalid City or Date\n')


class Generator:
    def __init__(self, length):
        self.length = length

    def __iter__(self):
        self.op = 0
        self.ip = 0
        return self
        # self.length = length

    def __next__(self):
        result = []
        if self.ip < self.length:
            result = [self.op, self.ip]
            self.ip = self.ip + 1
        else:
            self.ip = 0
            self.op = self.op + 1
            if(self.op < self.length):
                result = [self.op, self.ip]
            else:
                raise StopIteration
        return result


class Generator2:
    def __init__(self, length):
        self.length = length

    def __iter__(self):
        self.ii = 0
        return self

    def __next__(self):
        result = self.ii
        self.ii = self.ii + 1
        if self.ii <= self.length:
            return result
        raise StopIteration


def producerTicket(generator, out_q):
    while True:
        lock.acquire()
        try:
            args = next(generator)
        except StopIteration:
            lock.release()
            break
        lock.release()
        line = ticket_lines[args].split(',')
        try:
            out_q.put((args, getTicketPrice(line[0], line[28], line[29], line[26], line[22])))
        except Exception:
            continue

def consumerTicket(out_q, ticket):
    while True:
        response = out_q.get()
        print('Processing line %d out of %d'%(response[0], len(ticket_lines)))
        result = extractTicketPrice(response[1])

        row = ticket_lines[response[0]].split(',')
        prefix = row[0] + ',' + row[2] + ',' + row[3] + ',' + row[4] + ',' + row[5] + ',' + row[6] + ',' + row[
            7] + ',' + row[8] + ',' + row[9] + ',' + row[10] + ',' + row[11] + ',' + row[12] + ',' + row[22] + ','
        for ii in result.keys():
            ticket.write(prefix)
            ticket.write(seat_price_ref[ii] + ',')
            ticket.write(str(result[ii]) + ',')
            num = ''
            if row[seat_file_index[ii] + 36] == '--':
                num = '-1'
            elif row[seat_file_index[ii] + 36] == '无':
                num = '0'
            elif row[seat_file_index[ii] + 36] == '有':
                num = '100'
            else:
                num = row[seat_file_index[ii] + 36]
            ticket.write(num + ',')
            train_available = ''
            if row[34] == '1':
                train_available = '0'
            else:
                train_available = '1'
            ticket.write(train_available)
            ticket.write('\n')

def extractTicketPrice(pr):
    """

    :param pr: price response
    :return:
    """
    result = {}
    outcome = json.loads(pr)
    if 'data' not in outcome.keys():
        return False
    outcome = outcome['data']
    if 'A9' in outcome.keys() and 'P' in outcome.keys():
        result['A9'] = '-1'
    else:
        if 'A9' in outcome.keys():
            # ignore ￥

            result['A9'] = outcome['A9'].replace('짜', '').replace('¥', '').replace('Â', '')
        else:
            if 'P' in outcome.keys():
                result['P'] = outcome['P'].replace('짜', '').replace('¥', '').replace('Â', '')
            else:
                result['P'] = '-1'
    if 'M' in outcome.keys():
        result['M'] = outcome['M'].replace('짜', '').replace('¥', '').replace('Â', '')
    else:
        result['M'] = '-1'
    if 'O' in outcome.keys():
        result['O'] = outcome['O'].replace('짜', '').replace('¥', '').replace('Â', '')
    else:
        result['O'] = '-1'
    if 'A6' in outcome.keys():
        result['6#3'] = outcome['A6'].replace('짜', '').replace('¥', '').replace('Â', '')
        if '6#1' in outcome.keys():
            result['6#1'] = str(int(outcome['6#1'])/10)
        else:
            result['6#1'] = '-1'
    else:
        result['6#3'] = '-1'
        result['6#1'] = '-1'
    if 'A4' in outcome.keys():
        result['4#3'] = outcome['A4'].replace('짜', '').replace('¥', '').replace('Â', '')
        if '4#1' in outcome.keys():
            result['4#1'] = str(int(outcome['4#1'])/10)
        else:
            result['4#1'] = '-1'
    else:
        result['4#3'] = '-1'
        result['4#1'] = '-1'
    if 'F' in outcome.keys():
        result['F#3'] = outcome['F'].replace('짜', '').replace('¥', '').replace('Â', '')
        if 'F#1' in outcome.keys():
            result['F#1'] = str(int(outcome['F#1'])/10)
        else:
            result['F#1'] = '-1'
    else:
        result['F#3'] = '-1'
        result['F#1'] = '-1'
    if 'A3' in outcome.keys():
        result['3#3'] = outcome['A3'].replace('짜', '').replace('¥', '').replace('Â', '')
        if '3#2' in outcome.keys():
            result['3#2'] = str(int(outcome['3#2'])/10)
        else:
            result['3#2'] = '-1'
        if '3#1' in outcome.keys():
            result['3#1'] = str(int(outcome['3#1'])/10)
        else:
            result['3#1'] = '-1'
    else:
        result['3#3'] = '-1'
        result['3#2'] = '-1'
        result['3#1'] = '-1'
    if 'A2' in outcome.keys():
        result['A2'] = outcome['A2'].replace('짜', '').replace('¥', '').replace('Â', '')
    else:
        result['A2'] = '-1'
    if 'A1' in outcome.keys():
        result['A1'] = outcome['A1'].replace('짜', '').replace('¥', '').replace('Â', '')
    else:
        result['A1'] = '-1'
    if 'WZ' in outcome.keys():
        result['WZ'] = outcome['WZ'].replace('짜', '').replace('¥', '').replace('Â', '')
    else:
        result['WZ'] = '-1'
    return result


target = [
    '北京',
    '上海',
    '广州',
    '深圳'
]

total_num = 0
lock = Lock()
name = 'ticket'
if __name__ == '__main__':
    url_q = Queue()
    dataset = open('./data/trainInfo.csv', 'w')
    dates = ['2020-05-21', '2020-05-22', '2020-05-23', '2020-05-24']
    station_code = getStationList()
    for date in dates:
        result_q = Queue()
        gnr = iter(Generator(100))
        total_num = len(station_code)*(len(station_code) - 1)
        threads = []
        for i in range(20):
            thread = Thread(target=producer, args=(gnr, result_q, ), daemon=True)
            threads.append(thread)
            thread.start()

        thread_p = Thread(target=consumer, args=(result_q, dataset, ), daemon=True)
        thread_p.start()
        # thread.join()
        for t in threads:
            t.join()

        while result_q.empty() is not True:
            response = json.loads(result_q.get())
            writeTrainInfo(dataset, response)
    dataset.close()
        # if name == 'ticket':
        # control flag [34]
    ticket = open('./data/ticketset.csv', 'w')
    file = open('./data/trainInfo.csv')
    ticket_lines = file.readlines()
    ticket_q = Queue()
    gnr2 = iter(Generator2(len(ticket_lines)))
    threads = []
    for i in range(20):
        thread = Thread(target=producerTicket, args=(gnr2, ticket_q, ), daemon=True)
        threads.append(thread)
        thread.start()

    thread_c = Thread(target=consumerTicket, args=(ticket_q, ticket, ), daemon=True)
    thread_c.start()

    for t in threads:
        t.join()

    while ticket_q.empty() is not True:
        response = ticket_q.get()
        result = extractTicketPrice(response[1])
        row = ticket_lines[response[0]].split(',')
        prefix = row[0] + ',' + row[2] + ',' + row[3] + ',' + row[4] + ',' + row[5] + ',' + row[6] + ',' + row[
            7] + ',' + row[8] + ',' + row[9] + ',' + row[10] + ',' + row[11] + ',' + row[12] + ',' + row[22] + ','
        for ii in result.keys():
            ticket.write(prefix)
            ticket.write(seat_price_ref[ii] + ',')
            ticket.write(str(result[ii]) + ',')
            num = ''
            if row[seat_file_index[ii] + 36] == '--':
                num = '-1'
            elif row[seat_file_index[ii] + 36] == '无':
                num = '0'
            elif row[seat_file_index[ii] + 36] == '有':
                num = '100'
            else:
                num = row[seat_file_index[ii] + 36]
            ticket.write(num + ',')
            train_available = ''
            if row[34] == '1':
                train_available = '0'
            else:
                train_available = '1'
            ticket.write(train_available)
            ticket.write('\n')

    ticket.close()