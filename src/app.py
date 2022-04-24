from dataclasses import field
from unittest import result
from webbrowser import get
from flask import Flask
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import false

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

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

resource_fields = {
    'id' : fields.Integer,
	'isbn': fields.String,
	'judul_buku': fields.String,
	'pengarang': fields.String,
	'tahun_terbit': fields.String,
	'qty_buku': fields.Integer
}

class get_all_buku(Resource):
    @marshal_with(resource_fields)
    def get(self):
        result = BukuModel.query.all()
        return result

class detail_buku(Resource):
    @marshal_with(resource_fields)
    def get(self, buku_id):
        result = BukuModel.query.filter_by(id=buku_id).first()
        if not result:
            abort(404, message="Could not find Buku with that id")
        return result

class add_buku(Resource):
    @marshal_with(resource_fields)
    def put(self):
        args = buku_put_args.parse_args()
        buku = BukuModel(isbn=args['isbn'], judul_buku=args['judul_buku'], pengarang=args['pengarang'], tahun_terbit=args['tahun_terbit'], qty_buku=args['qty_buku'])
        db.session.add(buku)
        db.session.commit()
        return buku, 200

# BUKU
api.add_resource(get_all_buku, "/buku")
api.add_resource(detail_buku, "/buku/<int:buku_id>")
api.add_resource(add_buku, "/buku/add")

if __name__ == "__main__":
	app.run(debug=True)