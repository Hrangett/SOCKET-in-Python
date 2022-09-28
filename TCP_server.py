
# 그런데 서버가 하나의 연결이 요청된 후, 바로 종료가 되었습니다.
# 이렇게 되면, 또 다른 클라이언트는 서버에 접속을 할 수 없겠네요.

# 그래서 서버는 요청을 받아들이는 부분, 즉 accept() 메서드를 호출하는 부분을 무한 루프로 처리하여 계속해서 연결을 받아주도록 하려고 합니다.
# 무한루프로 계속 요청을 받아들이는 것은 좋은데, 그러면 서버는 요청을 받아들이는 역할만 하고 끝나겠네요.
# 요청을 받아들인 이후의 동작, 예를 들어 클라이언트와 채팅을 주고 받는다든지, 파일을 전송한다든지 등의 과정은 할 수 없게 됩니다.
# TCPServer의 메인 메서드는 무한루프를 돌면서 요청을 계속 받아들이고, 요청이 오면 새로운 쓰레드를 생성하여 각 클라이언트들과 통신을 할 수 있도록 하는 개선이 필요합니다


import socket
import threading
from queue import Queue


def socket_def():
    IP = '127.0.0.1'
    PORT = 5555

    NMEA_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    NMEA_socket.connect((IP, PORT))
    return NMEA_socket

#checksum 검사
def calcul_checksum(befor_cal):
    nums = 0

    for cal_bytes in befor_cal:
        nums ^= cal_bytes       #xor연산
    return format(nums, 'X')


#Serial 통신을 통한 NMEA 값 receive
def NMEA_Recv(NMEA_server, send_queue):
    try:

        while 1:
            # line = NMEA_server.recv(1024)
            # print("recv -> ", line)
            # if count <1:
            #     continue
            line = NMEA_server.recv(1024)
            # print("recv -> ", line)
            # print(type(send_queue))
            split_01 = (line.decode('utf-8')).split("$")        #byte -> string 후 특정 문자열을 기준으로 문자열 분리 :: 방법을 더 줄일 수 있지 안ㅎ을까?
            split_02 = split_01[1].split('*')                   #chechsum result 이전까지 문자열 추출

            checksum_befor_cal = bytes(split_02[0], 'utf-8')    #string #checksum_befor_cal = split_02[0]
            checksum_result =split_02[1][:2]                    #문자열
            checksum_result = checksum_result
            calcul_result = calcul_checksum(checksum_befor_cal)    # 함수로 전달(bytes), 결과값 저장(string), 0x이후의 데이터부터 저장,

            # print(type(split_02[0]))


            if (checksum_result == calcul_result):                 #string 형식은 대소문자 구분됨, 아스키코드로 값 비교
                send_queue.put(split_02[0])
                pass
    except OSError as e:
        print(e)


#Clients 정보 송신
def Send(group, send_queue):
    print("Thread Send start")
    # print(type(send_queue))

    try:
        while True:

            recv = send_queue.get()
            # print('recv => ', recv)
            if recv == 'change':
                break
                #새 클라이언트가 담긴 group list를 기반으로, 새로운 스레드를 생성. 기존에 존재하는 스레드는 종료.

                #비동기

            for client in group:
                #접속한 client 나갔을 경우, 접속해있는 client 에게로 메세지 전달이 안됨. 수정 요망
                #데이터를 받은 후 사순환을 종료합니다.recv () 함수가 막히지 않도록 클라이언트 (파일 송신자) 를 닫기 전에 서버 (파일 수신자) 에게 "연결을 끊겠습니다" 라는 메세지를 보내고 양쪽 모두 close 할 것을 권장
                # if not client: continue
                
                try:
                    # print(f"client info ->{client} \r\n")
                    msg = 'GPS Code -> ' + recv + '\r\n'
                    client.send(bytes(msg.encode()))
                except:
                    print("001")
                    group.remove(client)
                    print("client      ", client)

    except:
        print("002")
if __name__ == '__main__':      # 이 모듈이 메인으로 사용될 시
    try:
        print("STart socket")
        send_queue = Queue()
        HOST = ''
        PORT = 9903

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP
        client_socket.bind((HOST, PORT))
        client_socket.listen()
        """
        {   client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP
        client_socket.bind((HOST, PORT))
        client_socket.listen() }         
        
        == client_soket = socket.create_server(HOST,PORT)        
        
        """

        count = 0
        group = []

        NMEA_server = socket_def()
        print("nmea thread 실행")
        #nmea 값 recive 하는 thread 생성
        nmea_thread = threading.Thread(target=NMEA_Recv, args=(NMEA_server,send_queue))
        nmea_thread.start()

        while True:

           conn, addr = client_socket.accept()  # 해당 소켓을 열고 대기
           group.append(conn)  # 연결된 클라이언트의 소켓정보
           # conn.close()
           count = count + 1

           print('Connected ' + str(addr))

           if count>1:
               send_queue.put("change")
               send_thread = threading.Thread(target=Send, args=(group, send_queue,)) #target = 함수명, argument = 전달 할 파라미터
               send_thread.start()

           else:
               send_thread = threading.Thread(target=Send, args=(group, send_queue,))
               send_thread.start()


    except OSError as e:
        print(e)

#server_socket.close()
#스크립트파일이 메인 프로그램으로 사용될 때와, 모듈로 사용될 때를 구분하기 위한 용도


