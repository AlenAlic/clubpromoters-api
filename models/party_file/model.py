from ext import db
from models.tables import TABLE_PARTY_FILES, TABLE_PARTY, TABLE_FILE


class PartyFile(db.Model):
    __tablename__ = TABLE_PARTY_FILES
    party_id = db.Column(db.Integer, db.ForeignKey(f'{TABLE_PARTY}.party_id', onupdate="CASCADE", ondelete="CASCADE"),
                         primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey(f'{TABLE_FILE}.file_id', onupdate="CASCADE", ondelete="CASCADE"),
                        primary_key=True)
    party = db.relationship("Party", backref=db.backref(TABLE_PARTY_FILES, cascade="all, delete-orphan"))
    file = db.relationship("File", backref=db.backref(TABLE_PARTY_FILES))
    order = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint('party_id', 'file_id', name='_party_file_uc'),)
