import socket
import ssl
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time

request_time = 0
total_requests = 0
start_time = time.time()

PORT = 5000
secure_sock = None

current_role = None
login_win = None


# ---------------- SEND ----------------
def send_command(cmd):
    global request_time, total_requests

    try:
        request_time = time.time()
        total_requests += 1

        secure_sock.send((cmd + "\n").encode())

    except:
        messagebox.showerror("Error", "Connection lost")


# ---------------- LOGIN SCREEN ----------------
def login_screen():
    win = tk.Toplevel(root)
    win.title("Login / Register")
    win.geometry("300x250")

    tk.Label(win, text="Username").pack(pady=5)
    user_entry = tk.Entry(win)
    user_entry.pack()

    tk.Label(win, text="Password").pack(pady=5)
    pass_entry = tk.Entry(win, show="*")
    pass_entry.pack()

    def do_login():
        u = user_entry.get().strip()
        p = pass_entry.get().strip()

        if not u or not p:
            messagebox.showerror("Error", "Enter username & password")
            return

        send_command(f"LOGIN {u} {p}")

    def do_register():
        u = user_entry.get().strip()
        p = pass_entry.get().strip()

        if not u or not p:
            messagebox.showerror("Error", "Enter username & password")
            return

        send_command(f"REGISTER {u} {p}")

    tk.Button(win, text="Login", command=do_login).pack(pady=10)
    tk.Button(win, text="Register", command=do_register).pack()

    return win


# ---------------- CONNECT ----------------
def connect_to_server():
    global secure_sock

    host = simpledialog.askstring("Server IP", "Enter Server IP Address:")

    if not host:
        messagebox.showerror("Error", "IP required")
        root.destroy()
        return

    try:
        context = ssl._create_unverified_context()
        sock = socket.create_connection((host, PORT))
        secure_sock = context.wrap_socket(sock, server_hostname=host)

        threading.Thread(target=receive_messages, daemon=True).start()

    except Exception as e:
        messagebox.showerror("Connection Error", str(e))
        root.destroy()


# ---------------- RECEIVE ----------------
def receive_messages():
    global current_role

    while True:
        try:
            data = secure_sock.recv(4096)
            if not data:
                break

            message = data.decode()

            # -------- PERFORMANCE METRICS --------
            latency = time.time() - request_time

            elapsed_time = time.time() - start_time
            throughput = total_requests / elapsed_time if elapsed_time > 0 else 0

# basic scalability (clients handled indirectly via throughput)
            scalability = throughput  # simple representation

            log_box.insert(tk.END,f"\n[METRICS] Latency: {latency:.4f}s | Throughput: {throughput:.2f} req/s\n")

            log_box.insert(tk.END, message + "\n")
            log_box.see(tk.END)

            # LOGIN SUCCESS
            if message.startswith("SUCCESS"):
                role = message.split()[1]
                current_role = role

                if login_win:
                    login_win.destroy()

                if role != "admin":
                    add_btn.config(state="disabled")
                    remove_btn.config(state="disabled")
                else:
                    add_btn.config(state="normal")
                    remove_btn.config(state="normal")

                root.after(300, lambda: send_command("LIST"))

            elif "REGISTER_SUCCESS" in message:
                log_box.insert(tk.END, "Registered successfully. Now login.\n")

            elif "REGISTER_FAIL" in message:
                log_box.insert(tk.END, "User already exists.\n")

            elif message.startswith("FAIL"):
                log_box.insert(tk.END, "Login failed.\n")

            elif "Item not available" in message:
                messagebox.showerror("Error", "Item not available")    

            # TABLE UPDATE
            if "AVAILABLE ITEMS" in message:
                root.after(0, lambda m=message: update_table(m))

        except:
            break


# ---------------- TABLE UPDATE ----------------
def update_table(data):
    table.delete(*table.get_children())

    lines = data.split("\n")
    index = 1

    for line in lines:
        if "|" in line and "." in line:
            try:
                left, bid_part, winner_part = line.split("|")

                _, name = left.split(".", 1)
                bid = bid_part.split(":")[1].strip()
                winner = winner_part.split(":")[1].strip()

                table.insert("", "end", values=(index, name.strip(), bid, winner))
                index += 1

            except:
                continue


# ---------------- ACTIONS ----------------
def place_bid():
    try:
        item = int(item_entry.get())
        amount = int(bid_entry.get())
    except:
        messagebox.showerror("Error", "Invalid input")
        return

    send_command(f"BID {item} {amount}")


def add_item():
    name = item_name_entry.get().strip()
    if not name:
        return
    send_command(f"ADD_ITEM {name}")


def remove_item():
    try:
        item = int(item_entry.get())
    except:
        return
    send_command(f"REMOVE_ITEM {item}")


# ---------------- GUI ----------------
root = tk.Tk()
root.title("Real-Time Auction System")
root.geometry("1100x650")
root.configure(bg="#1e1e1e")

main_frame = tk.Frame(root, bg="#1e1e1e")
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# LEFT TABLE
left_frame = tk.Frame(main_frame, bg="#1e1e1e")
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

table = ttk.Treeview(left_frame,
                     columns=("ID", "Item", "Bid", "Winner"),
                     show="headings")

for col in ("ID", "Item", "Bid", "Winner"):
    table.heading(col, text=col)
    table.column(col, anchor="center", width=150)

table.pack(fill=tk.BOTH, expand=True)

# RIGHT PANEL
right_frame = tk.Frame(main_frame, bg="#2e2e2e", width=350)
right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

log_box = tk.Text(right_frame, height=15, bg="black", fg="lime")
log_box.pack(fill=tk.X, padx=10, pady=10)

controls = tk.Frame(right_frame, bg="#2e2e2e")
controls.pack(pady=10)

def make_label(text):
    return tk.Label(controls, text=text, bg="#2e2e2e", fg="white")

def make_entry():
    return tk.Entry(controls, width=30)

def make_button(text, cmd, color):
    return tk.Button(controls, text=text, command=cmd,
                     bg=color, fg="white", width=25)

make_label("Item ID").pack(pady=5)
item_entry = make_entry()
item_entry.pack()

make_label("Bid Amount").pack(pady=5)
bid_entry = make_entry()
bid_entry.pack()
make_button("Place Bid", place_bid, "#2196F3").pack(pady=8)

make_label("New Item").pack(pady=5)
item_name_entry = make_entry()
item_name_entry.pack()

add_btn = make_button("Add Item", add_item, "#9C27B0")
add_btn.pack(pady=5)

remove_btn = make_button("Remove Item", remove_item, "#f44336")
remove_btn.pack(pady=5)

make_button("Refresh", lambda: send_command("LIST"), "#607D8B").pack(pady=10)


# ---------------- START ----------------
def open_login():
    global login_win
    login_win = login_screen()

def start_app():
    connect_to_server()
    root.after(500, open_login)

root.after(200, start_app)

root.mainloop()