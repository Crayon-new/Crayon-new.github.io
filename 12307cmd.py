from functions.searchTicket import *
from model import engine_url

import sys, getopt, getpass
import prettytable

if __name__=='__main__':
    m = Manager(engine_url)
    print("Welcome to 12307!")
    case = 0
    while True:
        if case == 0:
            in1 = input("Please select\n"
              "1. Log in\n"
              "2. Sign in\n"
              "3. Exit")
            user_name = input("User Name:")
            user_pwd = getpass.getpass("Password:(Invisible)")
            if in1 == '1':
                user = m.validate(user_name, user_pwd)
                if user != False:
                    print("Logged in Successfully! Dear " + user.user_type)
                    case = case + 1
                else:
                    print("Wrong User Name or Password! Please Try Again")
            elif in1 == '2':
                user = m.createUser(pUser.create(user_name, user_pwd))
                if user != False:
                    print("User created!")
                else:
                    print("Invalid User Name or Password! Please try again")

        if case == 1:
            in1 = input("Functions to use:\n"
                        "1. Search Train\n"
                        "2. Alter information\n"
                        "3. Log out\n")
            dt = input("Date: (YYYYMMDD)")
            fs = input("From:")
            ts = input("TO:")
            res = m.search(dt, fs, ts, None)

            tb = prettytable.PrettyTable(list(res[0].keys()))
            for row in res:
                tb.add_row(list(row._asdict().values()))
            print(tb)
            break