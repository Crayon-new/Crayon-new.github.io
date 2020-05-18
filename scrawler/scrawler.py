import requests, re
import json
import time

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
    'gg':'其他'
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

def getTicketPrice(train_num, de_station_no, ar_station_no, seat_types, date):
    url = 'https://www.12306.cn/kfzmpt/leftTicket/queryTicketPrice?'
    url = url + 'train_no=' + train_num \
            + '&from_station_no=' + de_station_no \
            + '&to_station_no=' + ar_station_no \
            + '&seat_types=' + seat_types \
            + '&train_date=' + date
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text

def getAllTrainInfo(date, file_path):
    station_code = getStationList()
    dataset = open(file_path, 'w')
    attributes = None
    rows = []
    cnt = 0
    total_num = len(station_code)
    for fs in station_code.keys():
        for ts in station_code.keys():
            cnt = cnt + 1
            print('Scrawling Percentage: %d / %d %% \n'%(cnt, total_num))
            if fs is not ts:
                response = getTrainInfo(date, fs, ts, station_code)
                response = json.loads(response)
                if('data' in response.keys()):
                    if(type(response['data']) is dict and 'datas' in response['data'].keys()):
                        print('Data obtained successfully\n')
                        if(attributes is  None):
                            attributes = list(response['data']['datas'][0].keys())
                            for elem in attributes:
                                dataset.write(elem + ',')
                            dataset.write('\n')
                        for row in response['data']['datas']:
                            for elem in row.values():
                                dataset.write(str(elem) + ',')
                            dataset.write('\n')
                else:
                    print('Invalid City or Date\n')
    return True

if __name__ == '__main__':
    print('hello')