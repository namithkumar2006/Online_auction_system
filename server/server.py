import socket, ssl, threading, time
from database import *

HOST="0.0.0.0"
PORT=5000

clients=[]
lock=threading.Lock()

# ---------------- BROADCAST ----------------
def broadcast(msg):
    for c in clients[:]:
        try:
            c.send((msg+"\n").encode())
        except:
            clients.remove(c)

# ---------------- SEND DATA ----------------
def send_data():
    items=get_items()

    msg="AVAILABLE ITEMS\n"

    for i in items:
        msg += f"{i[0]}. {i[1]} | Highest Bid: {i[2]} | Winner: {i[3]}\n"

    broadcast(msg)

# ---------------- HANDLE CLIENT ----------------
def handle(c):
    ip = c.getpeername()[0]
    print(f"[CONNECTED] Client connected from {ip}")
    user=None
    role=None

    clients.append(c)

    try:
        while True:
            data=c.recv(1024).decode().strip()

            if not data:
                break

            parts=data.split()
            cmd=parts[0]

            # ---------------- REGISTER ----------------
            if cmd=="REGISTER":
                if len(parts)<3:
                    c.send(b"REGISTER_FAIL\n")
                    continue

                ok=register_user(parts[1],parts[2])

                if ok:
                    c.send(b"REGISTER_SUCCESS\n")
                else:
                    c.send(b"REGISTER_FAIL\n")

            # ---------------- LOGIN ----------------
            elif cmd=="LOGIN":
                if len(parts)<3:
                    c.send(b"FAIL\n")
                    continue

                r=login_user(parts[1],parts[2])

                if r:
                    user=parts[1]
                    role=r[0]

                    c.send(f"SUCCESS {role}\n".encode())

                    # send items after login
                    send_data()
                else:
                    c.send(b"FAIL\n")

            # ---------------- LIST ----------------
            elif cmd=="LIST":
                send_data()

            # ---------------- BID ----------------
            elif cmd=="BID":
                if not user:
                    c.send(b"Login first\n")
                    continue

                item=int(parts[1])
                amt=int(parts[2])

                found = False

                with lock:
                    for i in get_items():
                        if i[0] == item:
                            found = True

                            if time.time() > i[4]:
                                c.send(b"Auction already ended\n")
                                break

                            if amt > i[2]:
                                update_bid(item, user, amt)
                                send_data()
                            else:
                                c.send(b"Bid too low\n")
                                break

                if not found:
                    c.send(b"Item not available\n")

            # ---------------- ADD ITEM ----------------
            elif cmd=="ADD_ITEM":
                if role!="admin":
                    c.send(b"Only admin can add items\n")
                    continue

                name=" ".join(parts[1:])
                add_item(name)
                send_data()

            # ---------------- REMOVE ITEM ----------------
            elif cmd=="REMOVE_ITEM":
                if role!="admin":
                    c.send(b"Only admin can remove items\n")
                    continue

                try:
                    item_id=int(parts[1])
                except:
                    c.send(b"Invalid ID\n")
                    continue

                remove_item(item_id)
                send_data()

    except:
        pass

    finally:
        print(f"[DISCONNECTED] Client disconnected from {ip}")
        c.close()
        if c in clients:
            clients.remove(c)

# ---------------- START SERVER ----------------
def start():
    init_db()
    insert_default_items()

    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain("ssl/cert.pem","ssl/key.pem")

    s=socket.socket()
    s.bind((HOST,PORT))
    s.listen()

    print("Server running...")

    while True:
        c,_=s.accept()
        c=ctx.wrap_socket(c,server_side=True)
        threading.Thread(target=handle,args=(c,)).start()



start()