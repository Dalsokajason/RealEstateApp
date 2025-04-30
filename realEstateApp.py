#imports
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
#from sqlalchemy.orm import aliased
from sqlalchemy import and_, func
from datetime import datetime
#import env file
from dotenv import load_dotenv
load_dotenv()
import os

#Define App
app = Flask(__name__)

#Configuration for mySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + os.getenv("USER") + ':' + os.getenv("PASS") + '@' +  os.getenv("HOST") + '/customer_relationship_management_system'

db = SQLAlchemy(app)

class Firm(db.Model):
    __tablename__ = 'Firms'
    firm_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)


class ContactInfo(db.Model):
    __tablename__ = 'ContactInfo'
    contactInfoID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phoneNumber = db.Column(db.String(20))
    email_address = db.Column(db.String(255))


class Agent(db.Model):
    __tablename__ = 'Agents'
    agentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    agent_client_contact_info_id = db.Column(db.Integer, db.ForeignKey('ContactInfo.contactInfoID'), unique=True, nullable=False)
    commission_rate = db.Column(db.Numeric(5,2), nullable=False)
    agent_firm_id = db.Column(db.Integer, db.ForeignKey('Firms.firm_id'), nullable=False)
    broker_id = db.Column(db.Integer, db.ForeignKey('Agents.agentID'))
    #Agent has contact info
    contact_info = db.relationship('ContactInfo')
    #Agent works for firm
    firm = db.relationship('Firm')
    #Agent can be a broker
    broker = db.relationship('Agent', remote_side=[agentID])


class Client(db.Model):
    __tablename__ = 'Clients'
    client_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    client_contact_info_id = db.Column(db.Integer, db.ForeignKey('ContactInfo.contactInfoID'), unique=True, nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('Agents.agentID'))

    #Client has contact info
    contact_info = db.relationship('ContactInfo')
    #Client represented by agent
    agent = db.relationship('Agent')


class Property(db.Model):
    __tablename__ = 'Properties'
    property_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    address = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    property_client_id = db.Column(db.Integer, db.ForeignKey('Clients.client_id'))

    #Property owned by client
    client = db.relationship('Client')


class Transaction(db.Model):
    __tablename__ = 'Transactions'
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    transaction_client_id = db.Column(db.Integer, db.ForeignKey('Clients.client_id'), nullable=False)
    transaction_agent_id = db.Column(db.Integer, db.ForeignKey('Agents.agentID'), nullable=False)
    transaction_property_id = db.Column(db.Integer, db.ForeignKey('Properties.property_id'), nullable=False)
    transaction_type = db.Column(db.Boolean, nullable=False)
    date = db.Column(db.Date, nullable=False)

    #Transaction involves client
    client = db.relationship('Client')
    #Transacion involves agent
    agent = db.relationship('Agent')
    #Transaction involves property
    property = db.relationship('Property')

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/signIn", methods=["POST"])
def signIn():
    userType = request.form['userType']
    userId = request.form['userId']

    if userType == 'agent':
        return redirect(url_for("agent_page", agent_id=userId))
    elif userType == 'client':
        return redirect(url_for("client_page", client_id=userId))
    else:
        return "User Not Found"
    
@app.route("/client_sign_up_page", methods=["GET", "POST"])
def client_sign_up_page():
    agents = Agent.query.all()
    return render_template("client_sign_up_page.html", agents=agents)

@app.route("/clientSignUp", methods=["POST"])
def clientSignUp():
    userName = request.form['userName']
    userPhone = request.form['userPhone']
    userEmail = request.form['userEmail']
    userAgentId = request.form['userAgentId']

    userMaxId = db.session.query(func.max(Client.client_id)).scalar()
    client_id = userMaxId + 1

    contactMaxId = db.session.query(func.max(ContactInfo.contactInfoID)).scalar()
    client_contact_info_id = contactMaxId + 1

    agent = Agent.query.get(userAgentId)
    agent_id = agent.agentID

    new_contactInfo = ContactInfo(
        contactInfoID=client_contact_info_id,
        phoneNumber=userPhone,
        email_address=userEmail
    )

    new_client = Client(
        client_id=client_id,
        name=userName,
        client_contact_info_id=client_contact_info_id,
        agent_id=agent_id
    )

    db.session.add(new_contactInfo)
    db.session.commit()
    db.session.add(new_client)
    db.session.commit()

    return redirect(url_for("client_page", client_id=client_id))

@app.route("/agent_sign_up_page", methods=["GET", "POST"])
def agent_sign_up_page():
    firms = Firm.query.all()
    return render_template("agent_sign_up_page.html", firms=firms)

@app.route("/agentSignUp", methods=["POST"])
def agentSignUp():
    userName = request.form['userName']
    userPhone = request.form['userPhone']
    userEmail = request.form['userEmail']
    userFirm = request.form['userFirm']
    userCommission = request.form['userCommission']

    agentMaxId = db.session.query(func.max(Client.client_id)).scalar()
    agentID = agentMaxId + 1

    contactMaxId = db.session.query(func.max(ContactInfo.contactInfoID)).scalar()
    agent_contact_info_id = contactMaxId + 1

    new_contactInfo = ContactInfo(
        contactInfoID=agent_contact_info_id,
        phoneNumber=userPhone,
        email_address=userEmail
    )

    new_agent = Agent(
        agentID=agentID,
        name=userName,
        agent_contact_info_id=agent_contact_info_id,
        commission_rate=userCommission,
        agent_firm_id=userFirm
    )

    db.session.add(new_contactInfo)
    db.session.commit()
    db.session.add(new_agent)
    db.session.commit()

    return redirect(url_for("agent_page", agent_id=agentID))

@app.route("/agent_page/<int:agent_id>")
def agent_page(agent_id):
    agent = Agent.query.get(agent_id)
    clients = Client.query.filter_by(agent_id=agent_id).all()
    transactions = Transaction.query.filter_by(transaction_agent_id=agent_id).all()

    return render_template("agent_page.html", agent=agent, clients=clients, transactions=transactions)

@app.route("/client_page/<int:client_id>", methods=["GET"])
def client_page(client_id):
    client = Client.query.get(client_id)
    properties = db.session.query(Property).outerjoin(Transaction).filter(
        Transaction.transaction_property_id == None).filter(
            Property.property_client_id == client_id).all()
    #properties = db.session.query(Property).join(Transaction,
     #   and_( 
      #  Property.property_id == Transaction.transaction_property_id,
       # Transaction.transaction_type == 1)).filter_by(transaction_client_id=client_id).all()
    #properties = db.session.query(Property).outerjoin(
     #   Transaction, and_(
      #      Property.property_id == Transaction.transaction_property_id,
       #     Transaction.transaction_type == 0
        #)
    #).all()
    #properties = Property.query.filter(Property.property_client_id==client_id, 
     #   ~Property.property_client_id.in_(
      #      db.session.query(Transaction.transaction_property_id).filter(
       #         Transaction.transaction_type == 1)
        #    )
    #).all()
    transactions = Transaction.query.order_by(Transaction.date.desc()).filter_by(transaction_client_id=client_id).all()

    return render_template("client_page.html", client=client, properties=properties, transactions=transactions)

@app.route("/client_page/<int:client_id>/addProperty", methods=["POST"])
def addProperty(client_id):
    propertyMaxId = db.session.query(func.max(Property.property_id)).scalar()
    property_id = propertyMaxId + 1
    address = request.form['address']
    price = float(request.form['price'])

    new_property = Property( 
        property_id=property_id,
        address=address, 
        price=price, 
        property_client_id=client_id)
    
    db.session.add(new_property)
    db.session.commit()

    return redirect(url_for('client_page', client_id=client_id))

@app.route("/removeProperty/<int:property_id>")
def removeProperty(property_id):
    property = Property.query.get(property_id)
    client_id = property.property_client_id
    db.session.delete(property)
    db.session.commit()

    return redirect(url_for('client_page', client_id=client_id))


@app.route("/agents")
def agents():
    agents = Agent.query.all()
    return render_template("agents.html", agents=agents)

@app.route("/properties")
def properties():
    properties = db.session.query(Property).outerjoin(Transaction).filter(
        Transaction.transaction_property_id == None).all()
    return render_template("properties.html", properties=properties)

@app.route("/purchase_property/<int:property_id>", methods=["GET", "POST"])
def purchase_property(property_id):
    property = Property.query.get(property_id)
    return render_template("purchase_property.html", property=property)

@app.route("/purchaseProperty/<int:property_id>", methods=["GET", "POST"])
def purchaseProperty(property_id):
    userId = request.form['userId']
    userName = request.form['userName']

    buyer = Client.query.get(userId)
    seller = Client.query.get(Property.query.get(property_id).property_client_id)
    property = Property.query.get(property_id)

    if userName != buyer.name:
        return "INVALID ACCOUNT"
    else:
        transactionMaxId = db.session.query(func.max(Transaction.transaction_id)).scalar()
        transaction_b_id = transactionMaxId + 1
        transaction_s_id = transaction_b_id + 1
        now = datetime.now()
        transaction_b = Transaction(
            transaction_id=transaction_b_id,
            transaction_client_id=buyer.client_id,
            transaction_agent_id=buyer.agent_id,
            transaction_property_id=property.property_id,
            transaction_type=1,
            date=now.strftime("%Y-%m-%d")
        )

        transaction_s = Transaction(
            transaction_id=transaction_s_id,
            transaction_client_id=seller.client_id,
            transaction_agent_id=seller.agent_id,
            transaction_property_id=property.property_id,
            transaction_type=0,
            date=now.strftime("%Y-%m-%d")
        )

        db.session.add(transaction_b)
        db.session.commit()
        db.session.add(transaction_s)
        db.session.commit()

        return redirect(url_for('properties'))


@app.route("/transactions")
def transactions():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template("transactions.html", transactions=transactions)

#debugger on
if __name__ in "__main__":
    app.run(debug=True)