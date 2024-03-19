import win32evtlog


def read_log(computer, logType="Application"):
    event_log = win32evtlog.OpenEventLog(computer, logType)

    hosts = []

    num = 0
    # TODO вынесит prev_rec_number в аргументы
    prev_rec_number = read_number()
    print(f'{prev_rec_number=}')
    last_event_number = 0

    last_record_number = 27775058564654313564613133213
    while last_record_number > prev_rec_number:
        # while num < 200:
        objects = win32evtlog.ReadEventLog(
            event_log, win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ, 0
        )
        if not objects:
            break

        for object in objects:
            if object.SourceName != 'MSExchangeFrontEndTransport':
                continue

            if object.StringInserts[0] != 'LogonDenied':
                continue

            # msg = win32evtlogutil.SafeFormatMessage(object, logType)

            if not last_event_number:
                last_event_number = object.RecordNumber
            last_record_number = object.RecordNumber
            if prev_rec_number == last_record_number:
                break

            ip = object.StringInserts[3]
            hosts.append(ip)

            print()
            print(ip, '***', f'{object.RecordNumber=}, {object.TimeWritten.strftime("%Y.%m.%d %H:%M:%S")}')

        num = num + len(objects)

    win32evtlog.CloseEventLog(event_log)

    return hosts, last_event_number


def save_number(last_record_number):
    with open('last_event_id.txt', 'w') as f:
        f.write(str(last_record_number))


def read_number():
    with open('last_event_id.txt', 'r') as f:
        return int(f.read())
