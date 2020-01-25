import pickle
import json
import os

from flask import Flask, render_template, flash, url_for, request, session, redirect
from dbutility import create_connection
from functools import wraps
from web3 import Web3
from datetime import timezone,datetime
from passlib.hash import sha256_crypt
import pyqrcode
from pyzbar import pyzbar
import cv2


def decoder(img_path):
    img = cv2.imread(img_path)
    barcodes = pyzbar.decode(img)
    for barcode in barcodes:
        (x, y, w, h) = barcode.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        print("[INFO] found {} barcode {}".format(barcodeType, barcodeData))
    return barcodeData


def generate_qr():
    link_img= "www.google.com"
    rand = random.randint(1001, 10001)
    url = pyqrcode.create(link_img)
    url.png('{}.png'.format(rand), scale=8)
    print("Printing QR code")
    return rand




class Node():
    def __init__(self,address,name,level,lat,lon,node_batchesn,no_batches):
        self.address = address
        self.name = name
        self.level = level
        self.location = {'lat':lat,'lon':lon}
        self.node_batches = node_batches
        self.no_batches = no_batches


app = Flask(__name__)
app.secret_key = 'its_super_secret'
app.static_folder = 'static'
endpoint = endpoint = 'HTTP://127.0.0.1:7545'
web3 = Web3(Web3.HTTPProvider(endpoint))
UPLOADS_FOLDER = 'static/uploads'
app.config['UPLOADS_FOLDER'] = UPLOADS_FOLDER

contract_address = '0x1e0707515B79fbBDd7E6e89a65aD3b33E0575828'

with open('abi.json') as f:
    abi = json.load(f)

SupplyChain = web3.eth.contract(address=contract_address,abi=abi)
chain_id = web3.eth.chainId

def get_node(address):
    data = SupplyChain.functions.viewNode(address).call()
    return Node(data[1],data[0],data[2],data[4],data[5],data[3],data[6])

def get_batch(id):
    data = SupplyChain.functions.viewBatch(id).call()
    print(data)
    return data

@app.route('/qr',methods=['POST'])
def qr():
    f = request.files['file']
    f.filename = 'temp.png'
    apath = os.path.join(app.config['UPLOADS_FOLDER'], f.filename)
    f.save(apath)
    data= decoder(apath)
    print(data)
    return redirect('/batch/'+data)

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/')
def index():
    flash('Our site uses cookies to store login info')
    return render_template('index.html')

@app.route('/nodes')
def nodes():
    node_ids= SupplyChain.functions.returnNodeAddress().call()
    nodes = []
    for id in node_ids:
        nodes.append(get_node(id))
        print(nodes) 
    return render_template('nodes.html',nodes=nodes)

@app.route('/node/<address>')
def node_view(address):
    node = get_node(address)
    return render_template('map.html',node=node)


@app.route('/batch/total')
def batches():
    batch_count= SupplyChain.functions.batchCount().call()
    batches = []
    for id in range(batch_count):
        batches.append(get_batch(id))
    print(batches)
    return render_template('batch.html',batches=batches)

@app.route('/batch/node')
def node_batches():
    node_account =  pickle.loads(session['data'][2])
    node_address = node_account['address']
    node_address = Web3.toChecksumAddress(node_address)
    print(node_address)
    batch_ids = SupplyChain.functions.returnNodeBatches(node_address).call()
    print(batch_ids)
    batches = []
    for id in batch_ids:
        print(id)
        batches.append(get_batch(id))
    print(batches)
    return render_template('batch.html',batches= batches)

@app.route('/batch/node/<add>')
def node_batche(add):
    batch_ids = SupplyChain.functions.returnNodeBatches(add).call()
    print(batch_ids)
    batches = []
    for id in batch_ids:
        print(id)
        batches.append(get_batch(id))
    print(batches)
    return render_template('batch.html',batches= batches)


@app.route('/admin/add-node')
def add_node():
    return render_template('create-node.html')

@app.route('/admin/add-batch')
def add_batch():
    return render_template('create-batch.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash("You have been logged out!")
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    print(request.form)
    c, _ = create_connection()
    c.execute('SELECT * FROM user WHERE email=? ',
              (request.form['email'],))
    data = c.fetchone()
    # print(data[1])
    if data and sha256_crypt.verify(request.form['password'], data[3]):
        session['logged_in'] = True
        session['data'] = data
        add = pickle.loads(session['data'][2])['address']
        session['address'] = Web3.toChecksumAddress(add)
        if data[1]=='admin@admin.com':
            session['admin'] = True
        flash('Welcome Back {}'.format(data[1]))
        return redirect(url_for('nodes'))
    else:
        flash('Invalid credentials')
        return redirect(url_for('index'))

@app.route('/addnode', methods=['POST'])
def addNode():
    if session['admin']:
        node_data = request.form
        print(node_data['password'])
        account = session['data'][2]
        su_account = pickle.loads(account)
        su_account = web3.eth.account.privateKeyToAccount(web3.eth.account.decrypt(su_account,'Admin@123'))
        print(su_account)
        nonce = web3.eth.getTransactionCount(su_account.address)
        node_acc = web3.eth.account.create()
        print(node_acc.address)
        encryted_node = web3.eth.account.encrypt(node_acc.privateKey,node_data['password'])
        node_pickle = pickle.dumps(encryted_node)
        password = sha256_crypt.hash(node_data['password'])
        c, conn= create_connection()
        c.execute(
            'INSERT INTO user (email,data,password) VALUES( ?, ?, ?)', (node_data['email'],node_pickle,password))
        conn.commit()
        trxn = SupplyChain.functions.addNode(node_data['name'],int(node_data['level']),node_data['lat'],node_data['lon'],node_acc.address).buildTransaction({
            'chainId':chain_id,
            'gas': 700000,
            'gasPrice': web3.toWei('1', 'gwei'),
            'nonce': nonce,
        })
        singed_trn = web3.eth.account.sign_transaction(trxn,private_key=su_account.privateKey)
        web3.eth.sendRawTransaction(singed_trn.rawTransaction)
        print('done')
        return redirect(url_for('nodes'))

@app.route('/addbatch', methods=['POST'])
def addBatch():
    if session['admin']:
        batch_data = request.form
        account = session['data'][2]
        su_account = pickle.loads(account)
        su_account = web3.eth.account.privateKeyToAccount(web3.eth.account.decrypt(su_account,'Admin@123'))
        nonce = web3.eth.getTransactionCount(su_account.address)
        timestamp = datetime.now().replace(tzinfo=timezone.utc).timestamp()
        print(batch_data)
        trxn = SupplyChain.functions.addBatch(batch_data['origin'],batch_data['name'],str(timestamp)).buildTransaction({
            'chainId':chain_id,
            'gas': 700000,
            'gasPrice': web3.toWei('1', 'gwei'),
            'nonce': nonce,
        })
        singed_trn = web3.eth.account.sign_transaction(trxn,private_key=su_account.privateKey)
        web3.eth.sendRawTransaction(singed_trn.rawTransaction)
        print('done')
        return render_template('batch.html')

@app.route('/batch/forward/<id>',methods=['POST'])
def forwardBatch(id):
    address = request.form['origin']
    timestamp = datetime.now().replace(tzinfo=timezone.utc).timestamp()
    SupplyChain.functions.forwardBatch(int(id),address,str(timestamp))
    return (id+address)
    
@app.route('/batch/accept/<id>',methods=['POST'])
def acceptBatch(id):
    node_account =  pickle.loads(session['data'][2])
    address = node_account['origin']
    timestamp = datetime.now().replace(tzinfo=timezone.utc).timestamp()
    SupplyChain.functions.acceptBatch(id,address,str(timestamp))
    return (id+address)

@app.route('/batch/<id>' )
def viewBatch(id):
    batch = get_batch(int(id))
    history = SupplyChain.functions.viewBatchHistory(int(id)).call()
    nodes = []
    tsa = [] 
    print(history)
    # tsd = [] 
    for stop in history:
        nodes.append(get_node(stop[0]))
        tsa.append(datetime.fromtimestamp(int(float(stop[1]))))
    print(nodes)
    print(tsa)
    return render_template('map-trace.html',nodes=nodes,tsa= tsa,size =len(nodes),batch = batch)

if __name__ == "__main__":
    app.run(debug=True,host = '0.0.0.0')