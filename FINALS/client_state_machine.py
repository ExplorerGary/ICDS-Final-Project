"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
import json
import rsa_utils as rsa
import indexer
class ClientSM:
    def __init__(self, s):
        public_key, private_key = rsa.generate_keypair(1024) 
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s
        self.private_key =  private_key
        self.my_public_key = public_key
        self.peer_public_keys = {}

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer, my_public_key):
        msg = json.dumps({"action":"connect", "target":peer, "my_public_key": my_public_key})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    self.to_name=peer
                    if self.connect_to(peer, self.my_public_key) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    # print(poem)
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    
                    try:
                      
                        self.to_name=peer_msg["from"]
                        self.peer_public_keys[self.to_name]=peer_msg["my_public_key"]
                        msg2 = json.dumps({"action":"exchange_key", "target":self.to_name, "my_public_key": self.my_public_key})
                     
                        mysend(self.s, msg2)
                       
                        self.to_name=peer_msg["from"]
                        self.peer_public_keys[self.to_name]=peer_msg["my_public_key"]
                        self.peer = peer_msg["from"]
                        self.out_msg += 'Request from ' + self.peer + '\n'
                        self.out_msg += 'You are connected with ' + self.peer
                        self.out_msg += '. Chat away!\n\n'
                        self.out_msg += '------------------------------------\n'
                        self.state = S_CHATTING
                    
                      
                        
                       
                    except KeyError:
                        pass
              
                
                   
                if peer_msg["action"] == "connect":
                   
                    
                    print(self.peer_public_keys)
                    

#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"


#==============================================================================
        elif self.state == S_CHATTING:
            
            if len(peer_msg) > 0:
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"]=="exchange_key":
                    self.to_name=peer_msg["from"]
                    
                    self.peer_public_keys[self.to_name]=peer_msg["public_key"]
                   
               
            
            if len(my_msg) > 0:
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
                     # my stuff going out
                peer_public_key=self.peer_public_keys[self.to_name]
                
                encryped_msg=rsa.encrypt(my_msg,self.peer_public_keys[self.to_name])  
                if my_msg == "request_to_start_a_game":
                    mysend(self.s, json.dumps({"action":"game", "from":"[" + self.me + "]"}))
                    
                # my stuff going out
                elif my_msg == "press_button_1":
                  
                    mysend(self.s, json.dumps({"action":"gaming", "from":"[" + self.me + "]", 'operation': 1}))
                elif my_msg == "press_button_2":
                    
                    mysend(self.s, json.dumps({"action":"gaming", "from":"[" + self.me + "]", 'operation': 2}))
                elif my_msg == "press_button_3":
                    mysend(self.s, json.dumps({"action":"gaming", "from":"[" + self.me + "]", 'operation': 3}))
                elif my_msg == "press_button_4":
                    mysend(self.s, json.dumps({"action":"gaming", "from":"[" + self.me + "]", 'operation': 4}))
                elif my_msg == "press_button_5":
                    mysend(self.s, json.dumps({"action":"gaming", "from":"[" + self.me + "]", 'operation': 5}))
                elif my_msg == "press_button_6":
                    mysend(self.s, json.dumps({"action":"gaming", "from":"[" + self.me + "]", 'operation': 6}))
                elif my_msg == "press_button_7":
                    mysend(self.s, json.dumps({"action":"gaming", "from":"[" + self.me + "]", 'operation': 7}))
                elif my_msg == "press_button_8":
                    mysend(self.s, json.dumps({"action":"gaming", "from":"[" + self.me + "]", 'operation': 8}))
                elif my_msg == "press_button_9":
                    mysend(self.s, json.dumps({"action":"gaming", "from":"[" + self.me + "]", 'operation': 9}))
                    
                
                else:
                    my_msg=encryped_msg                    
                    mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
               
            if len(peer_msg) > 0:    # peer's stuff, coming in
               
                if peer_msg["action"] == "connect":
                    self.out_msg += "(" + " joined)\n"
                    
                elif peer_msg["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                elif peer_msg["action"]=="exchange":

                    decryped=rsa.decrypt(peer_msg["message"],self.private_key)
                    self.out_msg += peer_msg["from"] + decryped
                    
                elif peer_msg['action'] == 'game':
                    if peer_msg['status'] == 'fail':
                        
                        self.out_msg += peer_msg['results']
                        
                    elif peer_msg['status'] == 'success':
                        self.out_msg += peer_msg['results']
                        
                        
                        
                
                
                
                elif peer_msg['action'] == 'gaming':
                    if peer_msg['status'] == 'continue':
                    
                        if peer_msg['operation'] == 1:
                            self.out_msg += "systeminfo1" + peer_msg['mark']
                            
                        elif peer_msg['operation'] == 2:
                            self.out_msg += "systeminfo2" + peer_msg['mark']
                        elif peer_msg['operation'] == 3:
                            self.out_msg += "systeminfo3" + peer_msg['mark']
                        elif peer_msg['operation'] == 4:
                            self.out_msg += "systeminfo4" + peer_msg['mark']
                        elif peer_msg['operation'] == 5:
                            self.out_msg += "systeminfo5" + peer_msg['mark']
                        elif peer_msg['operation'] == 6:
                            self.out_msg += "systeminfo6" + peer_msg['mark']
                        elif peer_msg['operation'] == 7:
                            self.out_msg += "systeminfo7" + peer_msg['mark']
                        elif peer_msg['operation'] == 8:
                            self.out_msg += "systeminfo8" + peer_msg['mark']
                        elif peer_msg['operation'] == 9:
                            self.out_msg += "systeminfo9" + peer_msg['mark']
                            
                    elif peer_msg['status'] == 'finish':
                        self.out_msg += "serverinfo" + peer_msg['result']
                        
                       
                    
             
                   

            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
