from user.model import User, Train, Ticket, Station, Order, ModelBase
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta

import hashlib
from random import Random
import time

class Manager:
    K_SUCCESS = 1
    K_FAILED = 0
    K_INVALID_USER = -1
    K_OVERLAPPED_TIME=-2

    def __init__(self, engine_url):
        self.engine_url = engine_url
        self.engine = create_engine(self.engine_url, pool_recycle=7200, pool_size=50, max_overflow=10)
        self.DBsession = sessionmaker(bind=self.engine)


    def search(self, searchDate, fs, ts):
        """
        :param searchDate: datetime object
        :param fs: string
        :param ts: string
        :param user: User table instance
        :return:
        """
        sd = searchDate
        session = self.DBsession()
        q0 = (session.query(
                            Ticket.ticket_id.label('ticket_id'),
                            Ticket.ticket_date.label('ticket_date'),
                            Train.train_name.label('Train_name'),
                            Ticket.depart_time.label('depart_time'),
                           Ticket.arrive_time.label('arrive_time'),
                            Ticket.day_difference.label('day_difference'),
                            Station.station_name.label('from_station_name'),
                            Ticket.seat_type.label('seat_type'),
                           Ticket.to_station_id.label('to_station_id'),
                            Ticket.num_of_tickets.label('num_of_tickets'),
                            Ticket.price.label('price'))
            .join(Station, Station.station_id==Ticket.from_station_id)
            .join(Train, Train.train_id==Ticket.train_id)
            .filter(Ticket.ticket_date==sd)
            .filter(Station.station_name.like(fs+'%'))
            .filter(Ticket.available_flag==True)
            .subquery('q0')
             )
        # sub0 = q0.subquery()
        q = (
            session.query(
                          q0.c.ticket_id.label('ticket_id'),
                          q0.c.ticket_date.label('ticket_date'),
                          q0.c.Train_name.label('train_name'),
                          q0.c.depart_time.label('depart_time'),
                          q0.c.arrive_time.label('arrive_time'),
                          q0.c.day_difference.label('day_difference'),
                          q0.c.from_station_name.label('from_station_name'),
                          Station.station_name.label('to_station_name'),
                          q0.c.seat_type.label('seat_type'),
                          q0.c.num_of_tickets.label('num_of_tickets'),
                          q0.c.price.label('price')
                          )
            .join(Station,
                  Station.station_id==q0.c.to_station_id
                  )
            .filter(Station.station_name.like(ts+'%'))
            .filter(q0.c.num_of_tickets!=-1)
            .order_by(asc(q0.c.depart_time))
            .order_by(desc(q0.c.Train_name))
            .distinct()
        )
        res = q.all()
        rl = []
        for row in res:
            rd = row._asdict()
            rd['price'] = rd['price']/10
            rl.append(rd)
        return rl

    @staticmethod
    def _getDateTime(dt, tm):
        return datetime.strptime(dt.strftime('%Y%m%d')+tm.strftime('%H%M'), '%Y%m%d%H%M')

    def reserve(self, ticket_id, user_name):
        """
        :param ticket_id: ticket_id of the selected
        :param user: id of user stored in User table
        :return: BOOLEAN, True for successful reservation, False for failed
        """
        session = self.DBsession()
        order = Order()
        order.ticket_id = ticket_id
        q = session.query(Ticket).filter_by(ticket_id=ticket_id)
        res = q.all()
        # depart datetime of the ticket to order
        dt_ticket = Manager._getDateTime(res[0].ticket_date, res[0].depart_time)
        # day difference of the ticket to order
        dd_ticket = timedelta(days=res[0].day_difference)
        at_ticket = Manager._getDateTime(res[0].ticket_date, res[0].arrive_time)+dd_ticket
        orders = self._checkOrders(user_name, session)
        for od in orders:
            if od.transaction_state==False:
                continue
            dd_order = timedelta(days=od.day_difference)
            dt_order = Manager._getDateTime(od.ticket_date, od.depart_time)
            at_order = Manager._getDateTime(od.ticket_date, od.arrive_time)+dd_order
            #  depart_c <= depart_o <= arrive_c
            condition1 = (dt_ticket >= dt_order) and (dt_ticket <= at_order)
            # depart_c <= arrive_0 <= arrive_c
            condition2 = (at_ticket <= at_order) and (at_ticket >= dt_order)
            if condition1 or condition2:
                return self.K_OVERLAPPED_TIME


        if len(res) != 1:
            raise Exception("No Ticket Found")
        order.user_id = self.userName2Id(user_name, session)
        order.transaction_state = True
        if order.user_id == False:
            return self.K_INVALID_USER
        order.transaction_time = datetime.now()
        ticket_num = res[0].num_of_tickets
        if ticket_num <= 0:
            return self.K_FAILED
        try:
            session.add(order)
            (session.query(Ticket)
             .filter_by(ticket_id=ticket_id)
             .update({Ticket.num_of_tickets:Ticket.num_of_tickets-1})
             )
            session.commit()
        except Exception:
            session.rollback()
            print("Order Failed")
            return self.K_FAILED
        return self.K_SUCCESS

    def refund(self, user_name, order_id):
        session = self.DBsession()
        q0 = (session.query(Order)
         .join(User, User.user_id==Order.user_id)
         .filter(User.user_name==user_name)
         .filter(Order.order_id==order_id)
        )
        res = q0.all()
        if res[0].transaction_state == False:
            return False
        if len(res) != 1:
            raise Exception("No Order Found")
        try:
            (session.query(Ticket)
             .filter(Ticket.ticket_id==res[0].ticket_id)
             .update({Ticket.num_of_tickets:Ticket.num_of_tickets+1}))
            (session.query(Order)
             .filter(Order.order_id==order_id)
             .update({Order.transaction_state:False}))
            session.commit()
        except Exception:
            return False
        session.close()
        return True

    @staticmethod
    def userName2Id(user_name, session):
        q0 = session.query(User).filter_by(user_name=user_name)
        res = q0.all()
        if len(res) != 1:
            return False
        return res[0].user_id

    def checkOrders(self, user_name, exhibit_finished=True):
        session = self.DBsession()
        res = self._checkOrders(user_name, session, exhibit_finished)
        rl = []
        for row in res:
            rd = row._asdict()
            rd['price'] = rd['price'] / 10
            rl.append(rd)
        session.close()
        return rl

    def _checkOrders(self, user_name, session, exhibit_finished=True):
        """
        :param user_name: name of the user
        :return: all the orders created by current user
        """
        # session = self.DBsession()
        user_id = self.userName2Id(user_name, session)
        if exhibit_finished:
            q0 = (
                session.query(Order.transaction_time.label('transaction_time'),
                              Order.transaction_state.label('transaction_state'),
                              Train.train_name.label('train_name'),
                              Station.station_name.label('from_station_name'),
                              Ticket.to_station_id.label('to_station_id'),
                              Order.order_id.label('order_id'),
                              Ticket.price.label('price'),
                              Ticket.seat_type.label('seat_type'),
                              Ticket.ticket_date.label('ticket_date'),
                              Ticket.depart_time.label('depart_time'),
                              Ticket.day_difference.label('day_difference'),
                              Ticket.arrive_time.label('arrive_time'))
                .filter(Order.user_id==user_id)
                .join(Ticket, Ticket.ticket_id==Order.ticket_id)
                .join(Train, Train.train_id==Ticket.train_id)
                .join(Station, Station.station_id==Ticket.from_station_id)
                .subquery('q0')
            )
        else:
            q0 = (
                session.query(Order.transaction_time.label('transaction_time'),
                              Order.transaction_state.label('transaction_state'),
                              Train.train_name.label('train_name'),
                              Station.station_name.label('from_station_name'),
                              Ticket.to_station_id.label('to_station_id'),
                              Order.order_id.label('order_id'),
                              Ticket.price.label('price'),
                              Ticket.seat_type.label('seat_type'),
                              Ticket.ticket_date.label('ticket_date'),
                              Ticket.depart_time.label('depart_time'),
                              Ticket.day_difference.label('day_difference'),
                              Ticket.arrive_time.label('arrive_time'))
                .filter(Order.user_id==user_id)
                .filter(Order.transaction_state==True)
                .join(Ticket, Ticket.ticket_id==Order.ticket_id)
                .join(Train, Train.train_id==Ticket.train_id)
                .join(Station, Station.station_id==Ticket.from_station_id)
                .subquery('q0')
            )
        q1 =(
            session.query(
                q0.c.transaction_time.label('transaction_time'),
                q0.c.transaction_state.label('transaction_state'),
                q0.c.train_name.label('train_name'),
                q0.c.ticket_date.label('ticket_date'),
                q0.c.order_id.label('order_id'),
                q0.c.day_difference.label('day_difference'),
                q0.c.depart_time.label('depart_time'),
                q0.c.arrive_time.label('arrive_time'),
                q0.c.seat_type.label('seat_type'),
                q0.c.price.label('price'),
                q0.c.from_station_name.label('from_station_name'),
                Station.station_name.label('to_station_name')
            )
            .join(Station, Station.station_id==q0.c.to_station_id)
            .order_by(asc(q0.c.ticket_date))
            .order_by(asc(q0.c.depart_time))
        )
        # session.close()
        res = q1.all()
        return res


    def validate(self, user_name, user_pwd):
        session = self.DBsession()
        q = session.query(User).filter_by(user_name=user_name)
        res = q.all()
        if len(res) != 1:
            session.close()
            return False
        if pUser.encrypt(user_pwd, res[0].user_pwd_salt)!=res[0].user_pwd:
            return False
        session.close()
        return res[0]

    def checkUserType(self, user_name):
        session = self.DBsession()
        q=session.query(User).filter(User.user_name==user_name)
        session.close()
        res = q.all()
        if len(res)!=1:
            session.close()
            return False
        session.close()
        return res[0]

    def createUser(self, user):
        """
        :param user: User(ModelBase) object
        :return: BOOLEAN
        """
        session = self.DBsession()
        q = session.query(User).filter_by(user_name=user.user_name)
        res = q.all()
        if len(res) != 0:
            session.close()
            return False
        try:
            session.add(user)
            session.commit()
        except Exception:
            session.rollback()
            return False
        return True

    def searchStationsOf(self, train_name):
        session = self.DBsession()
        q0 = (
            session.query(Station.station_id.label('station_id'),
                          Station.station_name.label('station_name'))
            .join(Ticket, (Station.station_id==Ticket.from_station_id)
                  | (Station.station_id==Ticket.to_station_id))
            .join(Train, Train.train_id==Ticket.train_id)
            .filter(Ticket.available_flag==True)
            .distinct()
            .order_by(asc(Station.station_id))
              )
        res = q0.all()
        session.close()
        return res

    def removeStationFrom(self, station_id, train_name):
        session = self.DBsession()
        try:
            train_id = session.query(Train).filter(Train.train_name==train_name).first().train_id
        except Exception:
            session.close()
            return self.K_FAILED
        q0 = (
            session.query(Ticket)
            .filter((Ticket.train_id==train_id)
                    & ((Ticket.from_station_id==station_id)
                    | (Ticket.to_station_id==station_id)))
        )
        res = q0.all()
        for row in res:
            (
                session.query(Order)
                .filter(row.ticket_id==Order.ticket_id)
                .update({Order.transaction_state: False})
             )
        q0.update({Ticket.available_flag:False})
        try:
            session.commit()
        except Exception:
            session.rollback()
            return False
        return True


    def createStation(self, station_code, station_name, city_name):
        session = self.DBsession()
        station = Station()
        station.station_name = station_name
        station.station_code = station_code
        station.city_name = city_name
        try:
            session.add(station)
            session.commit()
        except Exception:
            session.rollback()
            return self.K_FAILED
        return self.K_SUCCESS

    # creates a new ticket in Ticket table
    def addTicketToTrain(self, train_date, start_s, end_s, from_s, to_s,
                         depart_t, arrive_t, day_diff, train_id,
                         num_of_tickets, seat_type, price):
        session = self.DBsession()
        new_row = Ticket()
        try:
            new_row.train_id = session.query(Train).filter_by(train_id=train_id).first().train_id
            new_row.start_station_id = session.query(Station).filter_by(station_name=start_s).first().station_id
            new_row.end_station_id = session.query(Station).filter_by(station_name=end_s).first().station_id
            new_row.from_station_id = session.query(Station).filter_by(station_name=from_s).first().station_id
            new_row.to_station_id = session.query(Station).filter_by(station_name=to_s).first().station_id
        except Exception:
            return self.K_FAILED
        new_row.ticket_date = train_date
        new_row.price = price*10
        new_row.num_of_tickets = num_of_tickets
        new_row.seat_type = seat_type
        new_row.available_flag = True
        new_row.depart_time = depart_t
        new_row.arrive_time = arrive_t
        new_row.day_difference = day_diff
        try:
            session.add(new_row)
            session.commit()
        except Exception:
            session.rollback()
            return self.K_FAILED
        return self.K_SUCCESS

    def updateTicketPrice(self, ticket_id, price):
        session = self.DBsession()
        try:
            (session.query(Ticket)
             .filter(Ticket.ticket_id==ticket_id)
             .update({Ticket.price: price})
             )
            session.commit()
        except Exception:
            session.rollback()
            return self.K_FAILED
        return self.K_SUCCESS

    def updateTicketNum(self, ticket_id, num_of_tickets):
        session = self.DBsession()
        try:
            (session.query(Ticket)
             .filter(Ticket.ticket_id==ticket_id)
             .update({Ticket.num_of_tickets: num_of_tickets})
             )
            session.commit()
        except Exception:
            session.rollback()
            return self.K_FAILED
        return self.K_SUCCESS

    def updateTicketState(self, ticket_id, state):
        session = self.DBsession()
        q0 = (
            session.query(Ticket)
            .filter(Ticket.ticket_id==ticket_id)
        )
        res = q0.all()
        for row in res:
            if (row.available_flag == True) and (state==False):
                (session.query(Order)
                 .filter(Order.ticket_id==ticket_id)
                 .update({Order.transaction_state: False})
                 )
        q0.update({Ticket.available_flag: False})
        try:
            session.commit()
        except Exception:
            session.rollback()
            return self.K_FAILED
        return self.K_SUCCESS


class pUser:
    @staticmethod
    def create(user_name, user_password, user_email):
        u = User()
        u.user_name = user_name
        u.user_pwd_salt = pUser.genSalt(8)
        u.user_pwd = pUser.encrypt(user_password, u.user_pwd_salt)
        u.user_email = user_email
        return u

    @staticmethod
    def encrypt(user_password, salt):
        sha256 = hashlib.sha256()
        # salt = pUser.genSalt(10)
        sha256.update(str.encode(user_password+salt, 'utf-8'))
        return sha256.hexdigest()

    @staticmethod
    def genSalt(length):
        r = Random(time.time_ns())
        res = int(r.random()*(10**(length)))
        return str(res)



class pSuperUser(pUser):
    @staticmethod
    def create(user_name, user_password, user_email):
        u = pUser.create(user_name, user_password, user_email)
        u.user_type = 'SuperUser'
        return u

class pPassenger(pUser):
    @staticmethod
    def create(user_name, user_password, user_email):
        u = pUser.create(user_name, user_password, user_email)
        u.user_type = 'Passenger'
        return u

if __name__ == '__main__':
    m = Manager('postgresql://checker:123456@127.0.0.1:5432/test')
    Order.__table__.drop(m.engine)
    User.__table__.drop(m.engine)

    ModelBase.metadata.create_all(m.engine)
    m.search('20200508', ' 北京', '上海')
    if m.createUser(pPassenger.create('night-gale', '000226', '2583942273@qq.com')):
        print("User created")
    else:
        print("User not created")
    if m.createUser(pSuperUser.create('night-admin', '000226', '2583942273@qq.com')):
        print("Super User created")
    else:
        print("Super user not created")
    user = pUser.create('night-gale', '000226', '2583942273@qq.com')
    res = m.validate('night-gale', '000226')
    res = m.reserve(1, 'night-gale')
    res = m.reserve(18, 'night-gale')
    res = m.refund('night-gale', 1)
    if res:
        print("Valid User")