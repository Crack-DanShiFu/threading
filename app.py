import hashlib
import json
import random
import string
import threading
import time
from queue import Queue
from threading import Lock
import numpy as np
import socketio
from flask import Flask, render_template, request, g, session
from flask_socketio import SocketIO, emit, join_room, send

import config

async_mode = None
app = Flask(__name__)
app.config.from_object(config)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)


@app.route('/')
def hello_world():
    return render_template('index.html', async_mode=socketio.async_mode)


@app.route('/cycleSession', methods=['POST'])
def cycle_session():
    session['cycle'] = request.form['cycle']
    return session['cycle']


@app.route('/sumThreadSession', methods=['POST'])
def sumthreadsession():
    session['sumThreadSession'] = request.form['sumThreadSession']
    session['calculate_num'] = request.form['calculate_num']
    print(session['calculate_num'])
    return session['sumThreadSession']


@app.route('/supply_source', methods=['POST'])
def supply_session():
    session['supply_source_speed'] = request.form['supply_source_speed']
    return session['supply_source_speed']


@app.route('/consumer_source', methods=['POST'])
def consumer_session():
    session['consumer_source_speed'] = request.form['consumer_source_speed']
    return session['consumer_source_speed']


def background_single_thread(room, cycle_s):
    """Example of how to send server generated events to clients."""
    count = 0
    print(room)
    arr = []
    brr = []
    for i in range(cycle_s):
        arr.append(np.random.rand(1000, 1000))
        brr.append(np.random.rand(1000, 1000))
    start = time.time()
    for a in arr:
        for b in brr:
            np.dot(a, b)
        count += (100 / cycle_s)
        socketio.emit('server_response',
                      {'count': count},
                      namespace='/single_thread', room=room)
    end = time.time()
    socketio.emit('run_time',
                  {'time': end - start},
                  namespace='/single_thread', room=room)
    socketio.close_room(room)


@socketio.on('connect', namespace='/single_thread')
def single_thread_connect():
    room = request.sid
    cycle_s = int(session.get('cycle'))
    join_room(room)
    thread = socketio.start_background_task(target=background_single_thread, room=room, cycle_s=cycle_s)


def get_info(qu, room, i):
    time.sleep(1)
    start = time.time()
    while not qu.empty():
        temp = qu.get(1)
        socketio.emit('server_response',
                      {'num': temp, 'i': i},
                      namespace='/multi_thread', room=room)
        time.sleep(0.5)
        print(temp)
    end = time.time()
    socketio.emit('run_time',
                  {'time': end - start, 'i': i},
                  namespace='/multi_thread', room=room)
    socketio.close_room(room)


def background_multi_thread(room, sumThread, calculate_num):
    qu = Queue()
    for i in range(calculate_num):
        qu.put(i)
    th = []
    for i in range(sumThread):
        t = threading.Thread(target=get_info, args=(qu, room, i))
        th.append(t)
    for i in th:
        i.start()
    for i in th:
        i.join()


@socketio.on('connect', namespace='/multi_thread')
def multi_thread_connect():
    room = request.sid
    sumThread = int(session.get('sumThreadSession'))
    calculate_num = int(session.get('calculate_num'))
    join_room(room)
    thread = socketio.start_background_task(target=background_multi_thread, room=room, sumThread=sumThread,
                                            calculate_num=calculate_num)


def supply(room, qu, speed):
    while not qu.full():
        for i in range(speed):
            qu.put(1)
        socketio.emit('q_size',
                      {'q_size': qu.qsize()},
                      namespace='/supply_consumer', room=room)
        time.sleep(1)


def consumer(room, qu, speed):
    while True:
        while not qu.empty():
            for i in range(speed):
                qu.get(1)
            socketio.emit('q_size', {'q_size': qu.qsize()},
                          namespace='/supply_consumer', room=room)

            time.sleep(1)


# def background_supply_consumer(room, supply_speed, consumer_speed):
# #     global qu
# #     qu = Queue()
# #     global th_of_supply, th_of_consumer
# #     th_of_supply = threading.Thread(target=supply, args=(room, qu, supply_speed))
# #     th_of_consumer = threading.Thread(target=consumer, args=(room, qu, consumer_speed))
# #     th_of_supply.start(),
# #     th_of_consumer.start(),


@socketio.on('connect', namespace='/supply_consumer')
def supply_consumer_connect():
    global qu
    qu = Queue(100)
    room = request.sid
    join_room(room)
    supply_speed = int(session.get('supply_source_speed', 0))
    consumer_speed = int(session.get('consumer_source_speed', 0))

    thread1 = socketio.start_background_task(target=supply, room=room, qu=qu, speed=supply_speed)
    thread2 = socketio.start_background_task(target=consumer, room=room, qu=qu, speed=consumer_speed)


if __name__ == '__main__':
    socketio.run(app)
