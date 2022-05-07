from dataclasses import field
from email import message
from enum import unique
from lib2to3.pgen2 import token
from operator import and_
from os import link
from unittest import result
from webbrowser import get
from xmlrpc.client import boolean

from flask import Flask, jsonify, request
from flask_mail import Mail, Message
from flask_restful import (Api, Resource, abort, fields, marshal, marshal_with,
                           reqparse, url_for)
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import Column, false, and_, Date, ForeignKey
from datetime import date, timedelta
from password_strength import PasswordPolicy, PasswordStats


app = Flask(__name__)
api = Api(app)
mail = Mail(app)

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmp/perpus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure Email Verification
secretEncodeDummy = URLSafeTimedSerializer('SecretTokenDummy!')
app.config.from_pyfile('config.cfg')
mail = Mail(app)

# password policy
policy = PasswordPolicy.from_names(
    length=8,  # min length: 8
    uppercase=1,  # need min. 1 uppercase letters
    numbers=1,  # need min. 1 digits
)

# ===== DATABASE MODELS =====


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
buku_put_args.add_argument(
    "isbn", type=str, help="ISBN is required", required=True)
buku_put_args.add_argument("judul_buku", type=str,
                           help="Judul Buku is required", required=True)
buku_put_args.add_argument("pengarang", type=str,
                           help="Pengarang is required", required=True)
buku_put_args.add_argument("tahun_terbit", type=str,
                           help="Tahun Terbit is required", required=True)
buku_put_args.add_argument(
    "qty_buku", type=int, help="Quantity Buku is required", required=True)

resource_fields_buku = {
    'id': fields.Integer,
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
mahasiswa_put_args.add_argument(
    "nim", type=str, help="NIM is required", required=True)
mahasiswa_put_args.add_argument(
    "nama", type=str, help="Nama is required", required=True)
mahasiswa_put_args.add_argument(
    "no_hp", type=str, help="No Hp is required", required=True)

resource_fields_mahasiswa = {
    'nim': fields.String,
    'nama': fields.String,
    'no_hp': fields.String
}


class PetugasModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama = db.Column(db.String(45), nullable=False)
    no_hp = db.Column(db.String(13), nullable=False)


petugas_put_args = reqparse.RequestParser()
petugas_put_args.add_argument(
    "nama", type=str, help="Nama is required", required=True)
petugas_put_args.add_argument(
    "no_hp", type=str, help="No Telp is required", required=True)

resource_fields_petugas = {
    'id': fields.Integer,
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
user_put_args.add_argument(
    "email", type=str, help="Email is required", required=True)
user_put_args.add_argument(
    "password", type=str, help="Password is required", required=True)

resource_fields_user = {
    'email': fields.String,
    'password': fields.String,
    'token': fields.String,
    'verify_status': fields.Boolean
}

resource_fields_user_sign_in = {
    'token': fields.String
}


class PeminjamanModel(db.Model):
    id_peminjaman = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tanggal_peminjaman = db.Column(db.Date, nullable=False)
    tanggal_kembali = db.Column(db.Date, nullable=False)
    denda = db.Column(db.Integer, nullable=False, default=0)
    nim_mahasiswa = db.Column(db.String(9), ForeignKey(SiswaModel.nim))
    id_petugas = db.Column(db.Integer, ForeignKey(PetugasModel.id))

    def json(self):
        return {'id_peminjaman': self.id_peminjaman, 'tanggal_peminjaman': self.tanggal_peminjaman, 'tanggal_kembali': self.tanggal_kembali, 'denda': self.denda, 'nim_mahasiswa': self.nim_mahasiswa, 'id_petugas': self.id_petugas}


peminjaman_put_args = reqparse.RequestParser()
peminjaman_put_args.add_argument(
    "nim_mahasiswa", type=str, help="NIM is required", required=True)
peminjaman_put_args.add_argument(
    "id_petugas", type=str, help="ID Petugas is required", required=True)

resource_fields_peminjaman = {
    'id_peminjaman': fields.Integer,
    'tanggal_peminjaman': fields.String,
    'tanggal_kembali': fields.String,
    'denda': fields.Integer,
    'nim_mahasiswa': fields.String,
    'id_petugas': fields.Integer
}


class PeminjamanDetailModel(db.Model):
    id_detail_peminjaman = db.Column(
        db.Integer, primary_key=True, autoincrement=True)
    id_peminjaman = db.Column(
        db.Integer, ForeignKey(PeminjamanModel.id_peminjaman))
    id_buku = db.Column(db.Integer, ForeignKey(BukuModel.id))

    def __str__(self):
        return f'id_detail: {self.id_detail_peminjaman}, id_peminjaman: {self.id_peminjaman}, id_buku: {self.id_buku}'


peminjaman_detail_put_args = reqparse.RequestParser()
peminjaman_detail_put_args.add_argument(
    "id_buku", type=int, help="ID BUKU is required", required=True)

resource_fields_peminjaman_detail = {
    'id_detail_peminjaman': fields.Integer,
    'id_peminjaman': fields.Integer,
    'id_buku': fields.Integer
}

resource_fields_peminjaman_data_list = {
    'id_peminjaman': fields.Integer,
    'tanggal_peminjaman': fields.String,
    'tanggal_kembali': fields.String,
    'denda': fields.Integer,
    'nim_mahasiswa': fields.String,
    'id_petugas': fields.Integer,
    'detail_data': fields.Nested(resource_fields_peminjaman_detail)
}

resource_fields_get_peminjaman = {
    'id_peminjaman': fields.Integer,
    'tanggal_peminjaman': fields.String,
    'tanggal_kembali': fields.String,
    'denda': fields.Integer,
    'nim_mahasiswa': fields.String,
    'id_petugas': fields.Integer
}


# ===== ENDPOINTS CONFIGURE =====

class get_all_buku(Resource):
    @marshal_with(resource_fields_buku)
    def get(self):
        headers = request.headers
        authorization = headers.get("Authorization")
        user = UserModel.query.filter_by(token=authorization).count()

        if(user == 1):
            return BukuModel.query.all(), 200
        else:
            abort(403, message="Forbidden: Authentication token doesn't exist")


class search_buku(Resource):
    @marshal_with(resource_fields_buku)
    def get(self):
        headers = request.headers
        query = request.args.get("q")
        authorization = headers.get("Authorization")
        user = UserModel.query.filter_by(token=authorization).count()

        if(user == 1):
            return BukuModel.query.filter(BukuModel.judul_buku.like(f"%{query}%")).all(), 200
        else:
            abort(403, message="Forbidden: Authentication token doesn't exist")


class detail_buku(Resource):
    @marshal_with(resource_fields_buku)
    def get(self, buku_id):
        headers = request.headers
        authorization = headers.get("Authorization")
        result = BukuModel.query.filter_by(id=buku_id).first()
        user = UserModel.query.filter_by(token=authorization).count()
        if (user == 1):
            if not result:
                abort(404, message="Not Found: Could not find Anything")
            return result
        else:
            abort(403, message="Forbidden: Authentication token doesn't exist")


class add_buku(Resource):
    @marshal_with(resource_fields_buku)
    def post(self):
        args = buku_put_args.parse_args()
        buku = BukuModel(isbn=args['isbn'], judul_buku=args['judul_buku'], pengarang=args['pengarang'],
                         tahun_terbit=args['tahun_terbit'], qty_buku=args['qty_buku'])
        try:
            db.session.add(buku)
            db.session.commit()
            return buku, 200
        except Exception:
            abort(400, message=f"Bad Request: Something went wrong!")


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
        mahasiswa = SiswaModel(
            nim=args['nim'], nama=args['nama'], no_hp=args['no_hp'])
        try:
            db.session.add(mahasiswa)
            db.session.commit()
            return mahasiswa, 200
        except Exception:
            abort(400, message=f"Bad Request: NIM already been used")


class add_petugas(Resource):
    @marshal_with(resource_fields_petugas)
    def post(self):
        args = petugas_put_args.parse_args()
        petugas = PetugasModel(nama=args['nama'], no_hp=args['no_hp'])
        try:
            db.session.add(petugas)
            db.session.commit()
            return petugas, 200
        except Exception as e:
            abort(400, message=f"Bad Request: Something went wrong {e}")


class detail_petugas(Resource):
    @marshal_with(resource_fields_petugas)
    def get(self, id_petugas):
        result = PetugasModel.query.filter_by(id=id_petugas).first()
        if not result:
            abort(404, message="Could not find anything")
        return result, 200


class add_peminjaman(Resource):
    @marshal_with(resource_fields_peminjaman)
    def post(self):
        args = peminjaman_put_args.parse_args()
        try:
            mahasiswa = SiswaModel.query.filter_by(
                nim=args['nim_mahasiswa']).first()
            petugas = PetugasModel.query.filter_by(
                id=args['id_petugas']).first()
            peminjaman = PeminjamanModel(tanggal_peminjaman=date.today(), tanggal_kembali=(
                date.today()) + timedelta(weeks=2), nim_mahasiswa=mahasiswa.nim, id_petugas=petugas.id)
            db.session.add(peminjaman)
            db.session.commit()
            return peminjaman, 201
        except Exception as e:
            abort(400, message=f"Bad Request: Something went wrong {e}")


class add_detail_peminjaman(Resource):
    @marshal_with(resource_fields_peminjaman_detail)
    def post(self, id_peminjaman):
        args = peminjaman_detail_put_args.parse_args()
        buku = BukuModel.query.filter_by(id=args['id_buku']).first()
        if (buku.qty_buku <= 0):
            abort(400, message=f"Bad Request: Buku Stock Not Available")
        try:
            peminjaman = PeminjamanModel.query.filter_by(
                id_peminjaman=id_peminjaman).first()
            peminjaman_detail = PeminjamanDetailModel(
                id_peminjaman=peminjaman.id_peminjaman, id_buku=buku.id)
            buku.qty_buku = buku.qty_buku - 1
            db.session.add(peminjaman_detail)
            db.session.commit()
            return peminjaman_detail, 201
        except Exception as e:
            abort(400, message=f"Bad Request: Something went wrong | {e}")


class get_detail_peminjaman(Resource):
    @marshal_with(resource_fields_peminjaman_detail)
    def get(self, id_peminjaman):
        result = PeminjamanDetailModel.query.filter_by(
            id_peminjaman=id_peminjaman).all()
        if not result:
            abort(404, message="Could not find anything")
        return result


class get_complete_data_peminjaman(Resource):
    @marshal_with(resource_fields_peminjaman_data_list)
    def get(self, id_peminjaman):
        peminjaman_result = PeminjamanModel.query.filter_by(
            id_peminjaman=id_peminjaman).first()
        if not peminjaman_result:
            abort(404, message="Could not find anything")

        detail_result = PeminjamanDetailModel.query.filter_by(
            id_peminjaman=id_peminjaman).all()
        result = {'id_peminjaman': peminjaman_result.id_peminjaman, 'tanggal_peminjaman': peminjaman_result.tanggal_peminjaman, 'tanggal_kembali': peminjaman_result.tanggal_kembali,
                  'denda': peminjaman_result.denda, 'nim_mahasiswa': peminjaman_result.nim_mahasiswa, 'id_petugas': peminjaman_result.id_petugas, 'detail_data': detail_result}
        return result


class sign_up(Resource):
    @marshal_with(resource_fields_user)
    def post(self):
        args = user_put_args.parse_args()
        checkUserAvability = UserModel.query.filter_by(
            email=args['email']).count()
        if (checkUserAvability >= 1):
            abort(400, message="Bad Request: Email already used")
        if policy.test(args['password']):
            abort(400, message="Bad Request: Password not strong enough | password atleast 8 characters, Has A digit, and Has Uppercase Letter")

        try:
            generated_token = secretEncodeDummy.dumps(
                args['email'], salt='email_verification')
            user = UserModel(
                email=args['email'], password=args['password'], token=generated_token)
            db.session.add(user)
            db.session.commit()

            # Send Email
            email = args['email']
            msg = Message('Verifikasi Email Perpustakaan',
                          sender='mohfahmi270@gmail.com', recipients=[email])
            link = url_for('confirm_email',
                           token=generated_token, _external=True)
            msg.body = f'Silahkan klik link berikut ini untuk memverifikasi akun anda: {link}'
            mail.send(msg)
            return user, 201
        except Exception as e:
            abort(400, message=f"Bad Request: Something went wrong {e}")


class sign_in(Resource):
    @marshal_with(resource_fields_user_sign_in)
    def post(self):
        args = user_put_args.parse_args()
        login = UserModel.query.filter(and_(
            UserModel.email == args['email'], UserModel.password == args['password'])).first()
        if not login:
            abort(
                400, message="Bad Request: Login Unsuccessfull Check email and password")

        if(login.verify_status == True):
            return login, 200
        else:
            abort(401, message="Unauthorized: User Not Verify")


@app.route('/confirm_email/<token>', methods=['GET'])
def confirm_email(token):
    try:
        secretEncodeDummy.loads(token, salt='email_verification', max_age=5)
        user = UserModel.query.filter_by(token=token).first()
        user.verify_status = True
        db.session.commit()
    except SignatureExpired:
        return jsonify({"message": "ERROR: Token Has Been Expired"}), 401
    except Exception as e:
        abort(400, message=f"Bad Request: Something went Wrong: {e}")
    return jsonify({"message": "OK: Email Have been successfully verify"}), 201

# ===== ENDPOINTS =====


# AUTH
api.add_resource(sign_up, "/signup")
api.add_resource(sign_in, "/signin")

# BUKU
api.add_resource(get_all_buku, "/buku")
api.add_resource(search_buku, "/buku/search")
api.add_resource(detail_buku, "/buku/<int:buku_id>")
api.add_resource(add_buku, "/buku")

# MAHASISWA
api.add_resource(get_all_mahasiswa, "/mahasiswa")
api.add_resource(detail_mahasiswa, "/mahasiswa/<nim>")
api.add_resource(add_mahasiswa, "/mahasiswa")

# PETUGAS
api.add_resource(detail_petugas, "/petugas/<int:id_petugas>")
api.add_resource(add_petugas, "/petugas")

# PEMINJAMAN
api.add_resource(add_peminjaman, "/peminjaman")
api.add_resource(add_detail_peminjaman, "/peminjaman/<int:id_peminjaman>")
api.add_resource(get_detail_peminjaman,
                 "/peminjaman/<int:id_peminjaman>/detail")
api.add_resource(get_complete_data_peminjaman,
                 "/peminjaman/data/<int:id_peminjaman>")

if __name__ == "__main__":
    app.run(debug=True)
