from flask import Flask, render_template,redirect,request, session,url_for
from flask_socketio import join_room,leave_room, send, SocketIO
import random
from string import ascii_uppercase

app=Flask(__name__)
app.config["SECRET_KEY"]="ABCD"
socketio= SocketIO(app)

rooms={}  #store infor of room, messages code and everything
def generate_unique_code(length):
    while True:
        code=""
        for _ in range(length):
            code+=random.choice(ascii_uppercase)
        if code not in rooms:
            break

    return code

@app.route("/",methods=["POST","GET"])
def home():
    session.clear()
    if request.method=="POST":
        name=request.form.get("name")
        code=request.form.get("code")
        join=request.form.get("join",False)
        create=request.form.get("create",False)

        if not name:
            return render_template("home.html",error="Please enter name",name=name, code=code)
        if join !=False and not code:
            return render_template("home.html", error="Please enter a room code",name=name, code=code)
        
        room=code
        if create != False:
            room=generate_unique_code(4)   #room contains the unique code of the room 
            rooms[room]={"members":0, "messages" :[]}   #dictionary with key as room number and value as other info
        elif code not in rooms:
            return render_template("home.html",error="Room doesnot exist",name=name, code=code)
        session["room"]=room
        session["name"]=name
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room=session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    return render_template("room.html",code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room=session.get("room")
    if room not in rooms:
        return
    content={
        "name":session.get("name"),
        "message":data["data"]
    }
    send(content,to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said:{data['data']}")


@socketio.on("connect")
def connect(auth):
    room=session.get("room")
    name=session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return 
    
    join_room(room)
    send({"name":name, "message": "has entered room"},to=room)
    rooms[room]["members"]+=1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room=session.get("room")
    name=session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"]-=1
        if rooms[room]["members"]<=0:
            del rooms[room]
    send({"name":name, "message": "has left room"},to=room)       
    print(f"{name} left room {room}")


if __name__=="__main__":
    socketio.run(app, debug=True)