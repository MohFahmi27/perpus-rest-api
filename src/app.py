from dataclasses import field
from enum import unique
from lib2to3.pgen2 import token
from os import link
from webbrowser import get
from xmlrpc.client import boolean

from flask import Flask, jsonify
from flask_mail import Mail, Message
from flask_restful import (Api, Resource, abort, fields, marshal, marshal_with,
                           reqparse, url_for)
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import false

app = Flask(__name__)
api = Api(app)
mail = Mail(app)

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Configure Email Verification
secretEncodeDummy = URLSafeTimedSerializer('SecretTokenDummy!')
app.config.from_pyfile('config.cfg')
mail = Mail(app)

class BukuModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(10), nullable=False)
    judul_buku = db.Column(db.String(100), nullable=False)
    pengarang = db.Column(db.String(50), nullable=False)
    tahun_terbit = db.Column(db.String(20), nullable=False)
    qty_buku = db.Column(db.Integer, nullable=False)

    def __repr__(self) -> str:
        return f"Buku(isbn = {self.isbn}, judul_buku = {self.judul_buku}, pengarang = {self.pengarang}, tahun_terbit = {self.tahun_terbit}, qty_buku = {self.qty_buku}"

buku_put_args = reqparse.RequestParser()
buku_put_args.add_argument("isbn", type=str, help="ISBN is required", required=True)
buku_put_args.add_argument("judul_buku", type=str, help="Judul Buku is required", required=True)
buku_put_args.add_argument("pengarang", type=str, help="Pengarang is required", required=True)
buku_put_args.add_argument("tahun_terbit", type=str, help="Tahun Terbit is required", required=True)
buku_put_args.add_argument("qty_buku", type=int, help="Quantity Buku is required", required=True)

resource_fields_buku = {
    'id' : fields.Integer,
	'isbn': fields.String,
	'judul_buku': fields.String,
	'pengarang': fields.String,
	'tahun_terbit': fields.String,
	'qty_buku': fields.Integer
}

class SiswaModel(db.Model):
    nim = db.Column(db.String(9), nullable=False,  primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    no_hp = db.Column(db.String(12), nullable=False)

    def __repr__(self) -> str:
        return f"Buku(nim_mahasiswa = {self.nim}, nama = {self.nama}, no_hp = {self.no_hp}"

mahasiswa_put_args = reqparse.RequestParser()
mahasiswa_put_args.add_argument("nim", type=str, help="NIM is required", required=True)
mahasiswa_put_args.add_argument("nama", type=str, help="Nama is required", required=True)
mahasiswa_put_args.add_argument("no_hp", type=str, help="No Hp is required", required=True)

resource_fields_mahasiswa = {
    'nim' : fields.String,
	'nama': fields.String,
	'no_hp': fields.String
}

class UserModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(45), nullable=False, unique=True)
    password = db.Column(db.String(45), nullable=False)
    token = db.Column(db.String(50), nullable=False)
    verify_status = db.Column(db.Boolean, default=False)

user_put_args = reqparse.RequestParser()
user_put_args.add_argument("email", type=str, help="Email is required", required=True)
user_put_args.add_argument("password", type=str, help="Password is required", required=True)

resource_fields_user = {
    'email' : fields.String,
	'password': fields.String,
	'token': fields.String,
	'verify_status': fields.Boolean
}    

resource_fields_user_sign_in = {
	'token': fields.String
}    
    
class get_all_buku(Resource):
    @marshal_with(resource_fields_buku)
    def get(self):
        return BukuModel.query.all()

class detail_buku(Resource):
    @marshal_with(resource_fields_buku)
    def get(self, buku_id):
        result = BukuModel.query.filter_by(id=buku_id).first()
        if not result:
            abort(404, message="Could not find Anything")
        return result

class add_buku(Resource):
    @marshal_with(resource_fields_buku)
    def post(self):
        args = buku_put_args.parse_args()
        buku = BukuModel(isbn=args['isbn'], judul_buku=args['judul_buku'], pengarang=args['pengarang'], tahun_terbit=args['tahun_terbit'], qty_buku=args['qty_buku'])
        db.session.add(buku)
        db.session.commit()
        return buku, 200

class get_all_mahasiswa(Resource):
    @marshal_with(resource_fields_mahasiswa)
    def get(self):
        return SiswaModel.query.all()

class detail_mahasiswa(Resource):
    @marshal_with(resource_fields_mahasiswa)
    def get(self, nim):
        result = SiswaModel.query.filter_by(nim=nim).first()
        if not result:
            abort(404, message="Could not find anything")
        return result

class add_mahasiswa(Resource):
    @marshal_with(resource_fields_mahasiswa)
    def post(self):
        args = mahasiswa_put_args.parse_args()
        mahasiswa = SiswaModel(nim=args['nim'], nama=args['nama'], no_hp=args['no_hp'])
        db.session.add(mahasiswa)
        db.session.commit()
        return mahasiswa, 200

class sign_up(Resource):
    @marshal_with(resource_fields_user)
    def post(self):
        args = user_put_args.parse_args()
        generated_token = secretEncodeDummy.dumps(args['email'], salt='email_verification')

        user = UserModel(email=args['email'], password=args['password'], token=generated_token)
        db.session.add(user)
        db.session.commit()

        # Send Email
        email = args['email']
        msg = Message('Verifikasi Email Perpustakaan', sender='mohfahmi270@gmail.com', recipients=[email])
        link = url_for('confirm_email', token=generated_token, _external=True)
        msg.body = f'Silahkan klik link berikut ini untuk memverifikasi akun anda: {link}'
        mail.send(msg)
        return user, 200

class sign_in(Resource):
    @marshal_with(resource_fields_user_sign_in)
    def post(self):
        args = user_put_args.parse_args()
        login = UserModel.query.filter_by(email=args['email'], password=args['password']).first()
        if not login:
            abort(404, message="User Doesn't Exist")

        if(login.verify_status == True):
            return login, 200
        else :
            abort(401, message="Login Unsuccessfull")

@app.route('/confirm_email/<token>', methods=['GET'])
def confirm_email(token):
    try:
        secretEncodeDummy.loads(token, salt='email_verification', max_age=3600)
        user = UserModel.query.filter_by(token=token).first()
        user.verify_status = True
        db.session.commit()
    except SignatureExpired:
        return jsonify({"message": "ERROR: Token Has Been Expired"}), 401
    return jsonify({"message": "OK: Email Have been successfully verify"}), 200

# AUTH
api.add_resource(sign_up, "/signup")
api.add_resource(sign_in, "/signin")

# BUKU
api.add_resource(get_all_buku, "/buku")
api.add_resource(detail_buku, "/buku/<int:buku_id>")
api.add_resource(add_buku, "/buku")

# MAHASISWA
api.add_resource(get_all_mahasiswa, "/mahasiswa")
api.add_resource(detail_mahasiswa, "/mahasiswa/<nim>")
api.add_resource(add_mahasiswa, "/mahasiswa")

if __name__ == "__main__":
	app.run(debug=True)
