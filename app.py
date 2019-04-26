import threading
import time
from queue import Queue
import numpy as np
import socketio
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, send

import config

async_mode = None
app = Flask(__name__)
# 引入配置文件
app.config.from_object(config)
# 设置session的key
app.config['SECRET_KEY'] = 'secret!'
# 初始化socketio
socketio = SocketIO(app, async_mode=async_mode)
# 用于标记抢占式线程状态.
preemptive_state = [0, 0, 0]


# index首页的路由
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


# 获取对应单线程处的ajax提交过来的循环次数参数，写入session
@app.route('/cycleSession', methods=['POST'])
def cycle_session():
    session['cycle'] = request.form['cycle']
    return session['cycle']


# 获取线程个数，写入session
@app.route('/sumThreadSession', methods=['POST'])
def sumthreadsession():
    session['sumThreadSession'] = request.form['sumThreadSession']
    session['calculate_num'] = request.form['calculate_num']
    return session['sumThreadSession']


# 获取生产者速度 写入session
@app.route('/supply_source', methods=['POST'])
def supply_session():
    session['supply_source_speed'] = request.form['supply_source_speed']
    return session['supply_source_speed']


# 获取消费者速度 写入session
@app.route('/consumer_source', methods=['POST'])
def consumer_session():
    session['consumer_source_speed'] = request.form['consumer_source_speed']
    return session['consumer_source_speed']


# 单线程运行的后台线程

def background_single_thread(room, cycle_s):
    """
    :param cycle_s:循环次数
    :type room: str room是request传过来的sid，每个session对应一个sid。用于区分浏览器打开的不同页面
    """
    count = 0
    print(room)
    arr = []
    brr = []
    # 准备2*cycle_s组 个1000 * 1000 的大矩阵
    # 两组 大矩阵 交替相乘即可得到cycle_s*cycle_s组不同结果，加大运算量
    for i in range(cycle_s):
        arr.append(np.random.rand(1000, 1000))
        brr.append(np.random.rand(1000, 1000))
    start = time.time()
    for a in arr:
        for b in brr:
            np.dot(a, b)
        # 每运行cycle_s次输出一次结果 用100/cycle_s 的原因是为了和前台对应的进度条100吻合，每次的步进保证跑完之后进度条为100
        count += (100 / cycle_s)
        # 向前台的socket发送当前进度数据
        socketio.emit('server_response',
                      {'count': count},
                      namespace='/single_thread', room=room)
    end = time.time()
    # 向前台的socket监听发送计时数据
    socketio.emit('run_time',
                  {'time': end - start},
                  namespace='/single_thread', room=room)
    # 关闭当前room
    socketio.close_room(room)


# 单线程模式所对应的connect namespace为 '/single_thread'
@socketio.on('connect', namespace='/single_thread')
def single_thread_connect():
    room = request.sid
    # 获取存储在session中的循环次数
    cycle_s = int(session.get('cycle'))
    # 开启房间。确保每个session在一个房间内完成
    join_room(room)
    # 开启一个后台线程用于跑模拟方法
    thread = socketio.start_background_task(target=background_single_thread, room=room, cycle_s=cycle_s)


#
def multi_th(qu, room, i):
    # 等待其他父线程完成start
    time.sleep(1)
    start = time.time()  # 计时
    while not qu.empty():
        temp = qu.get(1)
        socketio.emit('server_response',
                      {'num': temp, 'i': i},
                      namespace='/multi_thread', room=room)
        # 假设每次的计算用时0.5s
        time.sleep(0.5)
        print(temp)
    end = time.time()
    # 推送计时数据到前台
    socketio.emit('run_time',
                  {'time': end - start, 'i': i},
                  namespace='/multi_thread', room=room)
    # 关闭房间
    socketio.close_room(room)


# 多线程模式下的后台线程
def background_multi_thread(room, sumThread, calculate_num):
    # 初始化一个全局队列，用于等下开启多线程是共享全局资源
    qu = Queue()
    for i in range(calculate_num):
        qu.put(i)
    # 创建一个线程队列
    th = []
    # 创建sumThread个线程
    for i in range(sumThread):
        # 将线程编号i 传入线程参数。用于向前台发送是哪个线程产生的数据
        t = threading.Thread(target=multi_th, args=(qu, room, i))
        th.append(t)
    # 启动线程
    for i in th:
        i.start()
    # for i in th:
    #     i.join()


# 多线程模式下对应的后台connect
@socketio.on('connect', namespace='/multi_thread')
def multi_thread_connect():
    # 获取房间号
    room = request.sid
    # 获取相关（要实现的线程数量，计算总量） 参数
    sumThread = int(session.get('sumThreadSession'))
    calculate_num = int(session.get('calculate_num'))
    join_room(room)
    # 开启有一个后台socketio线程
    thread = socketio.start_background_task(target=background_multi_thread, room=room, sumThread=sumThread,
                                            calculate_num=calculate_num)


# 生产者函数，用于按照一定速度向队列中加入值
def supply(room, qu, speed):
    while not qu.full():
        # 没1s加入的数量
        for i in range(speed):
            qu.put(1)
        #     并且向前台推送当前数量
        socketio.emit('q_size',
                      {'q_size': qu.qsize()},
                      namespace='/supply_consumer', room=room)
        time.sleep(1)


def consumer(room, qu, speed):
    while True:
        while not qu.empty():
            # 每1s消费speed个资源
            for i in range(speed):
                qu.get()
            #     并且向前台推送当前数量
            socketio.emit('q_size', {'q_size': qu.qsize()},
                          namespace='/supply_consumer', room=room)
            time.sleep(1)


# 消费者生产者模式对应的connect
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


# 抢占式线程1 优先级最低
def preemptive1(room):
    count = 0
    preemptive_state[0] = 1  # 更新状态
    start = time.time()
    while count < 100:
        # 判断其他线程的状态.如果有优先级高于本线程的运行则终止本线程
        if preemptive_state[1] is 1 or preemptive_state[2] is 1:
            continue
        count += 1
        time.sleep(0.2)
        # 向前台更新此线程进度
        socketio.emit('count1', {'count1': count},
                      namespace='/preemptive1', room=room)
    end = time.time()
    # 向前台更新此线程用时
    socketio.emit('count1_run_time', {'time': end - start},
                  namespace='/preemptive1', room=room)
    # 线程执行完成.更新标记
    preemptive_state[0] = 0


# 抢占式线程2 优先级中
def preemptive2(room):
    count = 0
    start = time.time()

    preemptive_state[1] = 1
    while count < 100:
        if preemptive_state[2] is 1:
            continue
        count += 1
        time.sleep(0.2)
        socketio.emit('count2', {'count2': count},
                      namespace='/preemptive2', room=room)
    end = time.time()
    socketio.emit('count2_run_time', {'time': end - start},
                  namespace='/preemptive2', room=room)
    preemptive_state[1] = 0


# 抢占式线程3 优先级最高
def preemptive3(room):
    count = 0
    start = time.time()

    preemptive_state[2] = 1
    while count < 100:
        count += 1
        time.sleep(0.2)
        socketio.emit('count3', {'count3': count},
                      namespace='/preemptive3', room=room)
    end = time.time()
    socketio.emit('count3_run_time', {'time': end - start},
                  namespace='/preemptive3', room=room)
    preemptive_state[2] = 0


# 抢占式线程1 对应的connect
@socketio.on('connect', namespace='/preemptive1')
def preemptive1_connect():
    room = request.sid
    join_room(room)
    thread1 = socketio.start_background_task(target=preemptive1, room=room)


# 抢占式线程2 对应的connect
@socketio.on('connect', namespace='/preemptive2')
def preemptive2_connect():
    room = request.sid
    join_room(room)
    thread1 = socketio.start_background_task(target=preemptive2, room=room)


# 抢占式线程3 对应的connect
@socketio.on('connect', namespace='/preemptive3')
def preemptive3_connect():
    room = request.sid
    join_room(room)
    thread1 = socketio.start_background_task(target=preemptive3, room=room)


if __name__ == '__main__':
    socketio.run(app)
