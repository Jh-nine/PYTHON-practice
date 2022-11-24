import socketserver # 여러형태의 소켓서버를 쉽게 구현하기 위해 사용
import threading

ip = "192.168.0.8"
port = 50001

# 스레드에서 데이터(자원) 경쟁을 막음
lock = threading.Lock()

# 클라이언트 유저 관리 클래스
class UserMangager:
    #생성자
    def __init__(self):
        self.users = {} #사용자 정보를 담을 딕셔너리 {닉네임 : (소켓, 주소)}
    
    # 새로운 사용자 추가(채팅 서버로 접속한 클라이언트 등록)
    def addUser(self, username, client_socket, address):
        #이미 등록된 사용자 처리
        if username in self.users:
            client_socket.send("이미 등록된 사용자입니다. \n".encode("UTF-8"))
            return
        
        #새로운 사용자 등록
        lock.acquire() #lock
        self.users[username] = {client_socket, address}
        lock.release() #unlock

        
        #모든 클라이언트에게 메시지 전송
        self.sendMessageToAll("[{}] 님이 입장하였습니다.".format(username))
        print("채팅 인원 : {} 명" .format(len(self.users)))

        return username

    # 등록된 사용자 제거
    def removeUser(self,username):
        if username not in self.users:
            return
        
        #새로운 사용자 삭제
        lock.acquire() #lock
        del self.users[username]
        lock.release() #unlock
    
    #수신한 메시지를 처리하는 함수
    def messageHandler(self, username, message):
        # 클라이언트 퇴장
        if message.strip()== '/exit':
            self.removeUser(username)
            return -1
        else :
            self.sendMessageToAll("[{}] : {}".format(username,message))
            return
    
    #모든 클라이언트에게 메시지 전송하는 함수
    def sendMessageToAll(self, message):
        for client_socket, address in self.users.values():
            client_socket.send(message.encode("UTF-8"))

# BaseRequestHandler 클라이언트의 모든 요청 처리
# - self.request : 클라이언트 소켓
# - self.client_address : 클라이언트 주소    
class TcpHandler(socketserver.BaseRequestHandler):
    #클라이언트 관리 객체 생성
    usermanager = UserMangager()
    
    #클라이언트 요청 처리하는 함수
    # BaseRequestHandler의 handle 함수 오버라이딩
    def handle(self):
        username = self.registerUsername()
        print("[{}] 연결 : {}".format(self.client_address[0],username))
        
        #예외처리
        try:
            message = self.request.recv(1024).decode("UTF-8")
            
            while message:
                if message.strip() != "/exit":
                    print("[{}] {} : {}".format(self.client_address[0],username, message))
                
                if self.usermanager.messageHandler(username,message) == -1:
                    self.request.close() #소켓 닫기
                    break
                
                #메시지 수신
                message = self.request.recv(1024).decode("UTF-8")
                
        except Exception as error:
            print("[에러발생]",error)
            
        print("[{}] 접속 종료" .format(self.client_address[0]))
        self.usermanager.removeUser(username)
        self.request.close()
    
    #클라이언트 닉네임 요청하는 함수
    def registerUsername(self):
        while True:
            self.request.send("닉네임 : ".encode("UTF-8"))
            username = self.request.recv(1024).decode("UTF-8").strip()
            
            # 새로운 클라이언트 등록
            if self.usermanager.addUser(username, self.request, self.client_address):
                return username

#TCP 채팅서버
# - ThreadingMixIn : 독립된 스레드로 처리하도록 접속할 때마다 새로운 스레드 생성
# - TCPServer : 클라이언트 연결 요청 처리
class Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

#직접실행
if __name__ == "__main__":
    print("[채팅서버 시작]")
    print("--- 종료 : Ctrl + C ---")
    
    #예외처리
    try:
        # TCP 채팅서버 객체 생성
        server = Server((ip,port),TcpHandler)
        
        #TCPServer.serve_ferever()
        # 클라이언트의 접속 요청 수신대기
        # 접속 요청 수락 후 BaseRequestHandler의 Handle 메소드 호출
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("[채팅 서버 종료]")
        server.shutdown() ## 채팅서버 셧다운
        server.server_close()
