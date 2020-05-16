# for ticket_num in Ticket, -1 represent no such ticket,
# -2 represent has ticket but the number of it is unknown
#
#
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Column, Integer, String, DateTime, create_engine, Date, ForeignKey, ForeignKeyConstraint, \
    PrimaryKeyConstraint, SmallInteger, Boolean, Sequence, UniqueConstraint, Time
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta, time
from operator import and_
# base class
ModelBase = declarative_base()
Base = automap_base()

engine_url = 'postgresql://checker:123456@127.0.0.1:5432/test'
engine = create_engine(engine_url, echo=True)
Base.prepare(engine, reflect=True)
tables = Base.classes
# Train = tables.train
# Station = tables.station
# Ticket = tables.ticket

DBSession = sessionmaker(bind=engine)
## initialized


class Train(ModelBase):
    __tablename__ = 'Train'
    train_id = Column(Integer, primary_key=True)
    train_num = Column(String(20), nullable=False, unique=True)
    train_name = Column(String(10), nullable=False)
    seat_type = Column(String(10), nullable=False)


class Ticket(ModelBase):
    __tablename__ = 'Ticket'

    ticket_id = Column(Integer, primary_key=True)
    ticket_date = Column(Date, nullable=False)
    train_id = Column(Integer, ForeignKey('Train.train_id'), nullable=False)
    depart_time = Column(Time, nullable=False)
    arrive_time = Column(Time, nullable=False)
    day_difference = Column(Integer, nullable=False)
    start_station_id = Column(Integer, ForeignKey('Station.station_id'), nullable=False)
    end_station_id = Column(Integer, ForeignKey('Station.station_id'), nullable=False)
    from_station_id = Column(Integer, ForeignKey('Station.station_id'), nullable=False)
    to_station_id = Column(Integer, ForeignKey('Station.station_id'), nullable=False)
    seat_type = Column(String(10), nullable=False)
    price = Column(Integer, nullable=True)
    num_of_tickets = Column(Integer, nullable=True)
    available_flag = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint('ticket_date', 'from_station_id', 'to_station_id', 'train_id', 'seat_type', 'depart_time'),
        {}
    )
    def query(From,To,date):
     station1 = session.query(Station).filter(Station.station_name==From).one()
     station2 = session.query(Station).filter(Station.station_name==To).one()
     Ti = session.query(Ticket).filter(Ticket.from_station_id==station1.station_id,Ticket.to_station_id==station2.station_id,Ticket.ticket_date==date,).all()
     return Ti
 

class Station(ModelBase):
    __tablename__ = 'Station'

    station_id = Column(Integer, primary_key=True)
    station_code = Column(String(10), nullable=False, unique=True)
    station_name = Column(String(20), nullable=False)
    city_name = Column(String(20), nullable=False)

session = DBSession()

def insertIntoTrain(train_num, train_name, seat_type):
    """
    :param table: tables int Base.classes
    :param row: a row represented by list
    :return:
    """
    new_row = Train()
    new_row.train_name = train_name
    new_row.train_num = train_num
    new_row.seat_type = seat_type
    q0 = session.query(Train).filter_by(train_name=train_name)
    if len(q0.all()) != 0:
        return False
    try:
        session.add(new_row)
        session.commit()
        # session.close()
    except Exception:
        session.rollback()
        session.close()
        return False
    session.close()
    return True

def insertIntoTicket(row_dict):
    """
    :param row_list:
    :return:
    """
    new_row = Ticket()
    # new_row.ticket_date = time.strptime(date, '%Y%m%d')
    new_row.ticket_date = row_dict['td']
    try:
        new_row.train_id = session.query(Train).filter_by(train_num=row_dict['tn']).first().train_id
        new_row.start_station_id = session.query(Station).filter_by(station_code=row_dict['ssc']).first().station_id
        new_row.end_station_id = session.query(Station).filter_by(station_code=row_dict['esc']).first().station_id
        new_row.from_station_id = session.query(Station).filter_by(station_code=row_dict['fsc']).first().station_id
        new_row.to_station_id = session.query(Station).filter_by(station_code=row_dict['tsc']).first().station_id
    except Exception:
        print("No available target id found")
        return False
    new_row.price = row_dict['price']
    new_row.num_of_tickets = row_dict['not']
    new_row.seat_type = row_dict['stype']
    new_row.available_flag = row_dict['taf']
    new_row.depart_time = row_dict['stime']
    new_row.arrive_time = row_dict['etime']
    new_row.day_difference = row_dict['df']
    # try:
    session.add(new_row)
    session.commit()
    # except Exception:
    #     session.rollback()
    #     session.close()
    #     return False
    session.close()
    return True


def insertIntoStation(station_code, station_name):
    new_row = Station()
    new_row.station_name = station_name
    new_row.station_code = station_code
    if station_name[-1] in ('东', '南', '西', '北'):
        new_row.city_name = station_name[:(len(station_name)-1)]
    else:
        new_row.city_name = station_name
    q0 = session.query(Station).filter_by(station_code=station_code)
    if len(q0.all()) != 0:
        return False
    try:
        session.add(new_row)
        session.commit()
        # session.close()
    except Exception:
        session.rollback()
        session.close()
        return False
    session.close()
    return True

def ticketLineToDict(line):
    elem = {}
    row = line.split(',')
    elem['tn'] = row[0]
    elem['ssc'] = row[1]
    elem['esc'] = row[3]
    elem['fsc'] = row[5]
    elem['tsc'] = row[7]
    elem['stime'] = datetime.strptime(row[9], '%H:%M').time()
    elem['etime'] = datetime.strptime(row[10], '%H:%M').time()
    # tdelta = timedelta(days=int(row[11]))
    # elem['etime'] = etime+tdelta
    elem['df'] = int(row[11])
    elem['td'] = datetime.strptime(row[12], "%Y%m%d").date()
    elem['stype'] = row[13]
    elem['price'] = int(float(row[14]) * 10)
    elem['not'] = int(row[15])
    elem['taf'] = bool(row[16])
    return elem


